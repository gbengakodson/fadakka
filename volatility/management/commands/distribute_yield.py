from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import random
from datetime import datetime, timedelta
from volatility.models import UserVolatilityToken, YieldDistribution, VolatilityToken


class Command(BaseCommand):
    help = 'Distribute monthly yield to volatility token holders (8-10%)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually distributing yield',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force distribution even if already done this month',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('🚀 YIELD DISTRIBUTION STARTED'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # Check if already distributed this month
        today = timezone.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if not force:
            existing = YieldDistribution.objects.filter(
                distributed_at__gte=month_start
            ).exists()

            if existing:
                self.stdout.write(
                    self.style.ERROR('❌ Yield already distributed this month. Use --force to override.')
                )
                return

        # Get all user token holdings with balance > 0
        user_tokens = UserVolatilityToken.objects.filter(balance__gt=0).select_related('user', 'token')

        total_tokens = user_tokens.count()
        if total_tokens == 0:
            self.stdout.write(self.style.WARNING('⚠️ No token holders found'))
            return

        self.stdout.write(f"📊 Found {total_tokens} token holdings to process")

        total_yield = Decimal('0')
        distributions = []

        for user_token in user_tokens:
            # Calculate monthly yield (8-10% random)
            yield_percentage = Decimal(str(random.uniform(8, 10)))
            yield_amount = user_token.balance * (yield_percentage / 100)

            # Calculate USD value
            usd_value = yield_amount * user_token.token.current_price

            self.stdout.write(f"\n{'=' * 40}")
            self.stdout.write(f"👤 User: {user_token.user.username}")
            self.stdout.write(f"   Token: {user_token.token.token_symbol}")
            self.stdout.write(f"   Balance: {user_token.balance:.4f}")
            self.stdout.write(f"   Yield: {yield_percentage:.2f}%")
            self.stdout.write(f"   Yield Amount: {yield_amount:.4f} {user_token.token.symbol}")
            self.stdout.write(f"   USD Value: ${usd_value:.2f}")

            if not dry_run:
                # Add yield to balance
                user_token.balance += yield_amount
                user_token.yield_earned_total += yield_amount
                user_token.last_yield_calculation = timezone.now()
                user_token.save()

                # Record distribution
                distribution = YieldDistribution.objects.create(
                    user_token=user_token,
                    amount=yield_amount,
                    percentage=yield_percentage,
                    usd_value=usd_value,
                    token_price=user_token.token.current_price
                )
                distributions.append(distribution)

                self.stdout.write(self.style.SUCCESS(f"   ✅ Yield added"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⏺️ [DRY RUN] Would add {yield_amount:.4f}"))

            total_yield += yield_amount

        self.stdout.write(self.style.WARNING('\n' + '=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('🔷 DRY RUN COMPLETED'))
            self.stdout.write(f"   Would distribute: {total_yield:.4f} total tokens")
            self.stdout.write(f"   To: {total_tokens} holdings")
        else:
            self.stdout.write(self.style.SUCCESS('✅ YIELD DISTRIBUTION COMPLETED'))
            self.stdout.write(f"   Total yield distributed: {total_yield:.4f} tokens")
            self.stdout.write(f"   To: {total_tokens} holdings")
            self.stdout.write(f"   Distributions recorded: {len(distributions)}")

            # Send email notification (optional)
            if settings.ENABLE_YIELD_EMAILS:
                self.send_notification_email(total_yield, total_tokens)

        self.stdout.write(self.style.WARNING('=' * 60))

    def send_notification_email(self, total_yield, total_users):
        """Send notification email about yield distribution"""
        subject = f'🎉 Monthly Yield Distributed - {timezone.now().strftime("%B %Y")}'
        message = f"""
        Hello Fadakka Admin,

        The monthly yield distribution has been completed.

        📊 Distribution Summary:
        • Total Yield: {total_yield:.4f} tokens
        • Total Holdings: {total_users}
        • Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}

        Check the admin panel for detailed distribution records.

        - Fadakka Index System
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )
        except:
            pass