from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from .models import UserVolatilityToken, YieldDistribution, HourlyYield, YieldSchedule


class YieldStatsView(APIView):
    """Get comprehensive yield statistics"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get user's tokens
        user_tokens = UserVolatilityToken.objects.filter(user=user)

        # Calculate total earned
        total_earned = YieldDistribution.objects.filter(
            user_token__user=user
        ).aggregate(total=Sum('usd_value'))['total'] or 0

        # Calculate today's earned
        today_earned = YieldDistribution.objects.filter(
            user_token__user=user,
            distributed_at__gte=today_start
        ).aggregate(total=Sum('usd_value'))['total'] or 0

        # Calculate current APY (average of last 30 days)
        last_30_days = YieldDistribution.objects.filter(
            user_token__user=user,
            distributed_at__gte=now - timedelta(days=30)
        ).aggregate(avg=Avg('percentage'))['avg'] or 9.2

        # Calculate monthly projection
        current_balance = sum(float(t.balance) * float(t.token.current_price) for t in user_tokens)
        monthly_projection = current_balance * 0.09  # 9% average

        # Next distribution time (random within next hour)
        next_minute = random.randint(1, 59)
        next_dist = f"in {next_minute}m"

        # Token breakdown
        token_breakdown = []
        for token in user_tokens:
            balance = float(token.balance)
            price = float(token.token.current_price)
            value = balance * price
            daily_yield = value * 0.09 / 30  # 9% monthly / 30 days
            monthly_proj = value * 0.09

            # Calculate progress for today
            today_schedule = YieldSchedule.objects.filter(
                user_token=token,
                day_of_month=now.day
            ).first()

            progress = 0
            if today_schedule and today_schedule.expected_amount > 0:
                progress = min(100,
                               float(today_schedule.distributed_amount) / float(today_schedule.expected_amount) * 100)

            token_breakdown.append({
                'symbol': token.token.token_symbol,
                'balance': balance,
                'value': value,
                'apy': round(random.uniform(8, 10), 1),
                'daily_yield': daily_yield,
                'monthly_projection': monthly_proj,
                'progress': round(progress, 1)
            })

        return Response({
            'total_earned': float(total_earned),
            'today_earned': float(today_earned),
            'current_apy': round(last_30_days, 1),
            'next_distribution': next_dist,
            'monthly_projection': float(monthly_projection),
            'token_breakdown': token_breakdown
        })


class HourlyYieldView(APIView):
    """Get hourly yield data for charts"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Get last 24 hours of yield
        hourly_data = []
        for i in range(24):
            hour_start = now.replace(hour=i, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            hour_yield = HourlyYield.objects.filter(
                user_token__user=user,
                distributed_at__range=[hour_start, hour_end]
            ).aggregate(total=Sum('usd_value'))['total'] or 0

            hourly_data.append({
                'hour': i,
                'usd_value': float(hour_yield),
                'time': f"{i:02d}:00"
            })

        return Response(hourly_data)


class DailyYieldView(APIView):
    """Get daily yield data for charts"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Get last 30 days of yield
        daily_data = []
        for i in range(30):
            day = now.day - i
            if day < 1:
                day += 30

            day_start = now.replace(day=day, hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_yield = YieldDistribution.objects.filter(
                user_token__user=user,
                distributed_at__range=[day_start, day_end]
            ).aggregate(total=Sum('usd_value'))['total'] or 0

            # Check if completed
            schedule = YieldSchedule.objects.filter(
                user_token__user=user,
                day_of_month=day
            ).first()

            completed = False
            if schedule and schedule.distributed_amount >= schedule.expected_amount:
                completed = True

            daily_data.append({
                'day': day,
                'yield': float(day_yield),
                'completed': completed
            })

        # Sort by day
        daily_data.sort(key=lambda x: x['day'])
        return Response(daily_data)