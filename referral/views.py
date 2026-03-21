# referral/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ReferralNode, NodeFeeDistribution, ReferralStats, ReferralLink
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class ReferralNetworkView(APIView):
    """View referral network and earnings"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            # Get or create referral node
            node, created = ReferralNode.objects.get_or_create(
                user=user,
                defaults={
                    'referral_code': self.generate_referral_code(user),
                    'level_1': [],
                    'level_2': [],
                    'level_3': [],
                    'level_4': [],
                    'level_5': [],
                    'level_6': [],
                    'level_7': []
                }
            )

            # Get or create referral stats
            stats, _ = ReferralStats.objects.get_or_create(user=user)

            # Get recent earnings
            recent_earnings = NodeFeeDistribution.objects.filter(
                to_user=user
            ).select_related('from_user', 'purchase').order_by('-distributed_at')[:10]

            # Get total earned (from stats or calculate)
            total_earned = float(stats.total_earned) if stats.total_earned else 0

            # Calculate downline counts from JSON fields
            downlines = {
                'level_1': len(node.level_1) if node.level_1 else 0,
                'level_2': len(node.level_2) if node.level_2 else 0,
                'level_3': len(node.level_3) if node.level_3 else 0,
                'level_4': len(node.level_4) if node.level_4 else 0,
                'level_5': len(node.level_5) if node.level_5 else 0,
                'level_6': len(node.level_6) if node.level_6 else 0,
                'level_7': len(node.level_7) if node.level_7 else 0,
            }

            # Format recent earnings
            earnings_data = []
            for earning in recent_earnings:
                earnings_data.append({
                    'from': earning.from_user.username if earning.from_user else 'Unknown',
                    'amount': float(earning.amount),
                    'level': earning.level,
                    'date': earning.distributed_at.strftime('%Y-%m-%d %H:%M'),
                    'percentage': float(earning.commission_percentage) if earning.commission_percentage else 0,
                    'node_fee': float(earning.node_fee_total) if earning.node_fee_total else 0
                })

            # Get monthly earnings chart data
            monthly_earnings = self.get_monthly_earnings(user)

            # Get leaderboard position
            leaderboard_position = self.get_leaderboard_position(user)

            # Get referral link click stats
            click_stats = self.get_click_stats(user)

            data = {
                'referral_code': node.referral_code,
                'total_earned': total_earned,
                'referral_link': f'https://fadakka.com/register?ref={node.referral_code}',
                'downlines': downlines,
                'recent_earnings': earnings_data,
                'monthly_earnings': monthly_earnings,
                'leaderboard_position': leaderboard_position,
                'click_stats': click_stats,
                'referrer': node.referrer.username if node.referrer else None,
                'pending_earnings': float(stats.pending_earnings) if stats.pending_earnings else 0,
                'active_referrals': stats.active_referrals if stats.active_referrals else 0,
                'conversion_rate': self.calculate_conversion_rate(user)
            }

        except Exception as e:
            logger.error(f"Error fetching referral data for {user.username}: {e}")
            # Return basic data if there's an error
            data = {
                'referral_code': f'FADAKKA_{user.id}',
                'total_earned': 0,
                'referral_link': f'https://fadakka.com/register?ref={user.id}',
                'downlines': {f'level_{i}': 0 for i in range(1, 8)},
                'recent_earnings': [],
                'error': str(e)
            }

        return Response(data)

    def generate_referral_code(self, user):
        """Generate a unique referral code"""
        import random
        import string
        base = user.username[:3].upper() if user.username else 'REF'
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{base}{random_part}"

    def get_monthly_earnings(self, user):
        """Get earnings for the last 6 months for chart"""
        monthly_data = []
        today = timezone.now()

        for i in range(5, -1, -1):  # Last 6 months
            month = today - timedelta(days=30 * i)
            month_start = month.replace(day=1, hour=0, minute=0, second=0)

            if i > 0:
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            else:
                month_end = today

            total = NodeFeeDistribution.objects.filter(
                to_user=user,
                distributed_at__gte=month_start,
                distributed_at__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'amount': float(total)
            })

        return monthly_data

    def get_leaderboard_position(self, user):
        """Get user's rank in referral earnings"""
        # Get all users with total_earned
        all_stats = ReferralStats.objects.filter(total_earned__gt=0).order_by('-total_earned')

        position = 1
        for stat in all_stats:
            if stat.user == user:
                break
            position += 1

        return {
            'position': position,
            'total_referrers': all_stats.count()
        }

    def get_click_stats(self, user):
        """Get referral link click statistics"""
        total_clicks = ReferralLink.objects.filter(referrer=user).count()
        unique_clicks = ReferralLink.objects.filter(referrer=user).values('ip_address').distinct().count()
        conversions = ReferralLink.objects.filter(referrer=user, converted_user__isnull=False).count()

        return {
            'total_clicks': total_clicks,
            'unique_clicks': unique_clicks,
            'conversions': conversions
        }

    def calculate_conversion_rate(self, user):
        """Calculate conversion rate for referral links"""
        clicks = ReferralLink.objects.filter(referrer=user).count()
        if clicks == 0:
            return 0

        conversions = ReferralLink.objects.filter(referrer=user, converted_user__isnull=False).count()
        return round((conversions / clicks) * 100, 2)


class ReferralEarningsDetailView(APIView):
    """Get detailed breakdown of referral earnings"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        level = request.query_params.get('level')
        days = request.query_params.get('days', 30)

        # Base queryset
        earnings = NodeFeeDistribution.objects.filter(to_user=user)

        # Filter by level if specified
        if level:
            earnings = earnings.filter(level=level)

        # Filter by days
        if days:
            cutoff = timezone.now() - timedelta(days=int(days))
            earnings = earnings.filter(distributed_at__gte=cutoff)

        # Get total by level
        level_breakdown = []
        for lvl in range(1, 8):
            level_total = earnings.filter(level=lvl).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            level_breakdown.append({
                'level': lvl,
                'total': float(level_total['total'] or 0),
                'count': level_total['count'] or 0
            })

        # Get recent transactions
        recent = earnings.select_related(
            'from_user', 'purchase__token'
        ).order_by('-distributed_at')[:20]

        recent_data = []
        for e in recent:
            recent_data.append({
                'id': e.id,
                'from_user': e.from_user.username if e.from_user else 'Unknown',
                'amount': float(e.amount),
                'level': e.level,
                'date': e.distributed_at.strftime('%Y-%m-%d %H:%M'),
                'token': e.purchase.token.token_symbol if e.purchase and hasattr(e.purchase, 'token') else 'Unknown',
                'node_fee': float(e.node_fee_total) if e.node_fee_total else 0,
                'percentage': float(e.commission_percentage) if e.commission_percentage else 0
            })

        return Response({
            'level_breakdown': level_breakdown,
            'recent_transactions': recent_data,
            'total_earned': float(earnings.aggregate(total=Sum('amount'))['total'] or 0),
            'total_transactions': earnings.count()
        })


class ReferralDownlineView(APIView):
    """Get detailed downline information"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            node = ReferralNode.objects.get(user=user)

            # Get detailed downline info for each level
            downline_details = {}

            for level in range(1, 8):
                level_field = f'level_{level}'
                user_ids = getattr(node, level_field, [])

                if user_ids:
                    # Get user details and their activity
                    users = User.objects.filter(id__in=user_ids).values('id', 'username', 'email', 'date_joined')

                    # Get earnings from this level
                    level_users = []
                    for user_data in users:
                        earnings = NodeFeeDistribution.objects.filter(
                            from_user_id=user_data['id'],
                            to_user=user,
                            level=level
                        ).aggregate(
                            total=Sum('amount'),
                            count=Count('id')
                        )

                        # Check if they're active (made any purchase)
                        has_purchases = NodeFeeDistribution.objects.filter(
                            from_user_id=user_data['id']
                        ).exists()

                        level_users.append({
                            'id': user_data['id'],
                            'username': user_data['username'],
                            'email': user_data['email'],
                            'joined': user_data['date_joined'].strftime('%Y-%m-%d'),
                            'earnings': float(earnings['total'] or 0),
                            'transactions': earnings['count'] or 0,
                            'active': has_purchases
                        })

                    downline_details[f'level_{level}'] = level_users
                else:
                    downline_details[f'level_{level}'] = []

            return Response({
                'total_downlines': sum(len(getattr(node, f'level_{i}', [])) for i in range(1, 8)),
                'downlines': downline_details
            })

        except ReferralNode.DoesNotExist:
            return Response({
                'total_downlines': 0,
                'downlines': {f'level_{i}': [] for i in range(1, 8)}
            })


class ReferralStatsView(APIView):
    """Get comprehensive referral statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            stats = ReferralStats.objects.get(user=user)
            node = ReferralNode.objects.get(user=user)

            # Calculate additional metrics
            total_downlines = sum(len(getattr(node, f'level_{i}', [])) for i in range(1, 8))

            # Get earnings by period
            today = timezone.now()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            earnings_week = NodeFeeDistribution.objects.filter(
                to_user=user,
                distributed_at__gte=week_ago
            ).aggregate(total=Sum('amount'))['total'] or 0

            earnings_month = NodeFeeDistribution.objects.filter(
                to_user=user,
                distributed_at__gte=month_ago
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Get top referrers (users who referred the most people)
            top_referrers = []
            top_nodes = ReferralNode.objects.exclude(level_1=[]).order_by('-level_1')[:5]
            for n in top_nodes:
                top_referrers.append({
                    'username': n.user.username,
                    'referrals': len(n.level_1) if n.level_1 else 0
                })

            # Get commission rate info
            commission_rates = [
                {'level': 1, 'rate': 100},
                {'level': 2, 'rate': 20},
                {'level': 3, 'rate': 10},
                {'level': 4, 'rate': 7},
                {'level': 5, 'rate': 5},
                {'level': 6, 'rate': 3},
                {'level': 7, 'rate': 1},
            ]

            return Response({
                'total_earned': float(stats.total_earned or 0),
                'total_referrals': stats.total_referrals or 0,
                'active_referrals': stats.active_referrals or 0,
                'pending_earnings': float(stats.pending_earnings or 0),
                'total_downlines': total_downlines,
                'earnings_week': float(earnings_week),
                'earnings_month': float(earnings_month),
                'level_breakdown': {
                    'level_1_count': stats.level_1_count or 0,
                    'level_2_count': stats.level_2_count or 0,
                    'level_3_count': stats.level_3_count or 0,
                    'level_4_count': stats.level_4_count or 0,
                    'level_5_count': stats.level_5_count or 0,
                    'level_6_count': stats.level_6_count or 0,
                    'level_7_count': stats.level_7_count or 0,
                    'level_1_earnings': float(stats.level_1_earnings or 0),
                    'level_2_earnings': float(stats.level_2_earnings or 0),
                    'level_3_earnings': float(stats.level_3_earnings or 0),
                    'level_4_earnings': float(stats.level_4_earnings or 0),
                    'level_5_earnings': float(stats.level_5_earnings or 0),
                    'level_6_earnings': float(stats.level_6_earnings or 0),
                    'level_7_earnings': float(stats.level_7_earnings or 0),
                },
                'commission_rates': commission_rates,
                'top_referrers': top_referrers
            })

        except (ReferralStats.DoesNotExist, ReferralNode.DoesNotExist):
            return Response({
                'total_earned': 0,
                'total_referrals': 0,
                'active_referrals': 0,
                'pending_earnings': 0,
                'total_downlines': 0,
                'earnings_week': 0,
                'earnings_month': 0,
                'level_breakdown': {},
                'commission_rates': [],
                'top_referrers': []
            })


class ReferralTreeView(APIView):
    """Get the complete referral tree visualization data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        max_depth = int(request.query_params.get('depth', 3))  # Limit depth for performance

        try:
            node = ReferralNode.objects.get(user=user)
            tree_data = self.build_tree(node, current_depth=1, max_depth=max_depth)
            return Response(tree_data)
        except ReferralNode.DoesNotExist:
            return Response({'error': 'Referral node not found'}, status=404)

    def build_tree(self, node, current_depth=1, max_depth=3):
        """Recursively build the referral tree"""
        if current_depth > max_depth:
            return None

        tree = {
            'id': node.user.id,
            'name': node.user.username,
            'code': node.referral_code,
            'earnings': float(node.total_earned),
            'depth': current_depth,
            'children': []
        }

        # Get downlines for next level
        next_level_field = f'level_{current_depth}'
        if hasattr(node, next_level_field):
            downline_ids = getattr(node, next_level_field, [])

            for user_id in downline_ids[:5]:  # Limit to 5 per level for performance
                try:
                    downline_node = ReferralNode.objects.get(user_id=user_id)
                    child_tree = self.build_tree(downline_node, current_depth + 1, max_depth)
                    if child_tree:
                        tree['children'].append(child_tree)
                except ReferralNode.DoesNotExist:
                    continue

        return tree


# Keep your original view for backward compatibility
class ReferralNetworkOriginalView(APIView):
    """Original mock view - kept for reference"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            'referral_code': f'FADAKKA_{request.user.id}',
            'total_earned': 125.50,
            'referral_link': f'https://fadakka.com/ref/{request.user.id}',
            'downlines': {
                'level_1': 3,
                'level_2': 7,
                'level_3': 12,
                'level_4': 8,
                'level_5': 4,
                'level_6': 2,
                'level_7': 1
            },
            'recent_earnings': [
                {'from': 'user123', 'amount': 5.20, 'level': 1, 'date': '2024-01-15'},
                {'from': 'user456', 'amount': 1.04, 'level': 2, 'date': '2024-01-14'},
                {'from': 'user789', 'amount': 0.52, 'level': 3, 'date': '2024-01-13'},
            ]
        }
        return Response(data)


# Add this at the end of your referral/views.py file

class ReferralRedirectView(APIView):
    """Handle clicks on referral links"""
    permission_classes = []  # Public endpoint - no authentication required

    def get(self, request, referral_code):
        try:
            # Verify referral code exists
            referrer_node = ReferralNode.objects.get(referral_code=referral_code)

            # Track the click
            ReferralLink.objects.create(
                referrer=referrer_node.user,
                referral_code=referral_code,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )

            # Store in session for conversion tracking
            request.session['referral_code'] = referral_code

        except ReferralNode.DoesNotExist:
            pass  # Invalid code, just redirect without tracking
        except Exception as e:
            # Log error but don't break the redirect
            print(f"Error tracking referral: {e}")

        # Redirect to frontend registration page
        # Make sure this URL matches your frontend
        frontend_url = "http://192.168.0.42:3000"  # Your React app URL
        return redirect(f"{frontend_url}/register?ref={referral_code}")