# wallet/views_kyc.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import KYCVerification
from .services.notification_service import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


class KYCStatusView(APIView):
    """Get KYC status for user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            kyc = KYCVerification.objects.get(user=request.user)
            return Response({
                'status': kyc.status,
                'submitted_at': kyc.submitted_at,
                'verified_at': kyc.verified_at,
                'can_withdraw_large': kyc.can_withdraw_large
            })
        except KYCVerification.DoesNotExist:
            return Response({
                'status': 'not_submitted',
                'can_withdraw_large': False
            })


class KYCSubmitView(APIView):
    """Submit KYC documents"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Check if already submitted
        if KYCVerification.objects.filter(user=request.user).exists():
            return Response(
                {'error': 'KYC already submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate required fields
        required_fields = ['full_name', 'date_of_birth', 'nationality', 'id_number', 'id_type']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate files
        if 'id_front' not in request.FILES:
            return Response(
                {'error': 'ID front image is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create KYC record
        kyc = KYCVerification.objects.create(
            user=request.user,
            status='pending',
            full_name=request.data['full_name'],
            date_of_birth=request.data['date_of_birth'],
            nationality=request.data['nationality'],
            id_number=request.data['id_number'],
            id_type=request.data['id_type'],
            id_front=request.FILES['id_front'],
            id_back=request.FILES.get('id_back'),
            selfie=request.FILES.get('selfie'),
            proof_of_address=request.FILES.get('proof_of_address')
        )

        # Send notification
        try:
            EmailNotificationService.send_kyc_verification_email(request.user, 'pending')
        except Exception as e:
            logger.error(f"KYC email failed: {e}")

        return Response({
            'success': True,
            'message': 'KYC documents submitted successfully',
            'status': 'pending'
        })


class KYCWithdrawCheckView(APIView):
    """Check if user can withdraw amount"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount', 0)
        try:
            amount = float(amount)
        except:
            return Response({'error': 'Invalid amount'}, status=400)

        # Define withdrawal limits
        DAILY_LIMIT_UNVERIFIED = 1000  # $1000 per day for unverified
        DAILY_LIMIT_VERIFIED = 50000  # $50000 per day for verified

        try:
            kyc = KYCVerification.objects.get(user=request.user)
            is_verified = kyc.status == 'verified'
        except KYCVerification.DoesNotExist:
            is_verified = False

        # Calculate today's withdrawals
        from .models import Transaction
        from django.utils import timezone
        from datetime import timedelta

        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_withdrawals = Transaction.objects.filter(
            user=request.user,
            transaction_type='withdrawal',
            status='completed',
            created_at__gte=today_start
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        daily_limit = DAILY_LIMIT_VERIFIED if is_verified else DAILY_LIMIT_UNVERIFIED
        remaining = daily_limit - today_withdrawals

        return Response({
            'can_withdraw': amount <= remaining,
            'daily_limit': daily_limit,
            'used_today': float(today_withdrawals),
            'remaining': float(remaining),
            'is_verified': is_verified,
            'requires_kyc': not is_verified and amount > DAILY_LIMIT_UNVERIFIED
        })