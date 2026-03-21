from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime
from volatility.models import UserVolatilityToken, YieldSchedule, HourlyYield, YieldDistribution


class Command(BaseCommand):
    help = 'Distribute hourly yield to vol_yield (non-compounding)'

    def handle(self, *args, **options):
        now = timezone.now()
        current_hour = now.hour
        current_day = now.day

        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING(f'⏰ HOURLY YIELD DISTRIBUTION - Hour {current_hour}'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # Get all active token holdings
        user_tokens = UserVolatilityToken.objects.filter(balance__gt=0).select_related('user', 'token')

        total_distributed = Decimal('0')
        distribution_count = 0

        for user_token in user_tokens:
            # Calculate monthly yield (8-10% of principal)
            monthly_rate = Decimal(str(random.uniform(8, 10))) / 100
            monthly_yield = user_token.balance * monthly_rate

            # Daily yield = monthly_yield / 30
            daily_yield = monthly_yield / 30

            # Hourly yield = daily_yield / 24
            hourly_yield = daily_yield / 24

            # Get or create schedule for today
            schedule, created = YieldSchedule.objects.get_or_create(
                user_token=user_token,
                day_of_month=current_day,
                defaults={
                    'expected_amount': daily_yield,
                    'status': 'pending'
                }
            )

            # Check if we've already distributed for this hour
            if HourlyYield.objects.filter(
                    schedule=schedule,
                    hour_of_day=current_hour
            ).exists():
                self.stdout.write(f"⏭️ Already distributed for {user_token.user.username} hour {current_hour}")
                continue

            # Add yield to vol_yield (NOT to balance - this is key!)
            user_token.vol_yield += hourly_yield
            user_token.yield_earned_total += hourly_yield
            user_token.save()

            # Create hourly distribution record
            hourly = HourlyYield.objects.create(
                user_token=user_token,
                schedule=schedule,
                hour_of_day=current_hour,
                amount=hourly_yield,
                usd_value=float(hourly_yield) * float(user_token.token.current_price),
                token_price=user_token.token.current_price,
                transaction_id=f"YIELD-{now.strftime('%Y%m%d%H%M%S')}-{user_token.id}"
            )

            # Update schedule
            schedule.distributed_amount += hourly_yield
            if schedule.distributed_amount >= schedule.expected_amount:
                schedule.status = 'completed'
            else:
                schedule.status = 'partial'
            schedule.save()

            # Record in main yield distribution
            YieldDistribution.objects.create(
                user_token=user_token,
                amount=hourly_yield,
                percentage=float(monthly_rate * 100),
                usd_value=float(hourly_yield) * float(user_token.token.current_price),
                token_price=user_token.token.current_price
            )

            total_distributed += hourly_yield
            distribution_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"✅ {user_token.user.username}: +{hourly_yield:.8f} yield (Principal: {user_token.balance:.4f})"
            ))

        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS(f'📊 SUMMARY'))
        self.stdout.write(f'   Hour: {current_hour}:00')
        self.stdout.write(f'   Distributions: {distribution_count}')
        self.stdout.write(f'   Total Yield: {total_distributed:.8f} tokens')
        self.stdout.write(self.style.WARNING('=' * 60))