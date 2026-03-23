from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer
from .models import Profile
from referral.models import ReferralNode, ReferralStats, ReferralLink
import random
import string
from django.utils import timezone
import logging
from wallet.models import GrandBalance

logger = logging.getLogger(__name__)


def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # Get referral code from query params or request data
        referral_code = request.query_params.get('ref') or request.data.get('ref')

        # Proceed with normal registration
        response = super().create(request, *args, **kwargs)

        if response.status_code == 201:
            user = User.objects.get(username=response.data['username'])

            # 👇 Create GrandBalance with ZERO balance (no free money!)
            GrandBalance.objects.create(
                user=user,
                balance_usdc=0,  # Start with zero
                total_deposited=0,
                total_withdrawn=0
            )
            print(f"✅ Created GrandBalance with $0 for {user.username}")


            # Create referral components
            self.create_referral_components(user, referral_code)

            # Add referral info to response
            response.data['referral'] = {
                'code': response.data.get('referral_code'),
                'referred_by': referral_code if referral_code else None
            }

        return response

    def create_referral_components(self, user, referral_code=None):
        """Create referral node and stats for new user"""
        try:
            # Generate unique referral code for the new user
            user_referral_code = generate_referral_code()

            # Create referral node
            node = ReferralNode.objects.create(
                user=user,
                referral_code=user_referral_code,
                level_1=[],
                level_2=[],
                level_3=[],
                level_4=[],
                level_5=[],
                level_6=[],
                level_7=[]
            )

            # Create referral stats
            stats = ReferralStats.objects.create(
                user=user,
                total_referrals=0,
                active_referrals=0,
                total_earned=0,
                pending_earnings=0
            )

            # Process referral if code exists
            if referral_code:
                self.process_referral_signup(user, referral_code, node)

            logger.info(f"Created referral components for user: {user.username}")

        except Exception as e:
            logger.error(f"Error creating referral components for {user.username}: {e}")

    def process_referral_signup(self, user, referral_code, user_node):
        """Process a signup with a referral code"""
        try:
            # Find the referrer by their referral code
            referrer_node = ReferralNode.objects.get(referral_code=referral_code)

            # Set referrer for new user
            user_node.referrer = referrer_node.user
            user_node.save()

            # Update referrer's level_1 list (direct referrals)
            if user.id not in referrer_node.level_1:
                referrer_node.level_1.append(user.id)
                referrer_node.save()

                # Update referrer's stats
                stats, _ = ReferralStats.objects.get_or_create(user=referrer_node.user)
                stats.level_1_count += 1
                stats.total_referrals += 1
                stats.save()

            # Track the referral link conversion
            ReferralLink.objects.filter(
                referral_code=referral_code,
                converted_user__isnull=True
            ).update(
                converted_user=user,
                converted_at=timezone.now()
            )

            logger.info(f"User {user.username} successfully referred by {referrer_node.user.username}")

        except ReferralNode.DoesNotExist:
            logger.warning(f"Invalid referral code during registration: {referral_code}")
        except Exception as e:
            logger.error(f"Error processing referral for {user.username}: {e}")


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        # Get or create referral components if they don't exist
        self.ensure_referral_components(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

    def ensure_referral_components(self, user):
        """Ensure user has referral components (for backward compatibility)"""
        try:
            ReferralNode.objects.get_or_create(
                user=user,
                defaults={
                    'referral_code': generate_referral_code(),
                    'level_1': [],
                    'level_2': [],
                    'level_3': [],
                    'level_4': [],
                    'level_5': [],
                    'level_6': [],
                    'level_7': []
                }
            )

            ReferralStats.objects.get_or_create(
                user=user,
                defaults={
                    'total_referrals': 0,
                    'active_referrals': 0,
                    'total_earned': 0,
                    'pending_earnings': 0
                }
            )
        except Exception as e:
            logger.error(f"Error ensuring referral components for {user.username}: {e}")


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'success': 'Logged out successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveAPIView):
    """Get user profile"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        # Ensure profile exists
        profile, created = Profile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'phone': '',
                'is_verified': False,
                'referral_code': generate_referral_code()
            }
        )

        # Also ensure referral components exist
        self.ensure_referral_components(self.request.user)

        return profile

    def ensure_referral_components(self, user):
        """Ensure user has referral components"""
        try:
            ReferralNode.objects.get_or_create(
                user=user,
                defaults={
                    'referral_code': generate_referral_code(),
                    'level_1': [],
                    'level_2': [],
                    'level_3': [],
                    'level_4': [],
                    'level_5': [],
                    'level_6': [],
                    'level_7': []
                }
            )

            ReferralStats.objects.get_or_create(
                user=user,
                defaults={
                    'total_referrals': 0,
                    'active_referrals': 0,
                    'total_earned': 0,
                    'pending_earnings': 0
                }
            )
        except Exception as e:
            logger.error(f"Error ensuring referral components for {user.username}: {e}")