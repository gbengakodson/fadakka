# volatility/tasks.py
from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import random
import logging
from django.core.management import call_command
from django.db import transaction
from .models import UserVolatilityToken, YieldDistribution, VolatilityToken
from wallet.models import GrandBalance

logger = logging.getLogger(__name__)


@shared_task
def update_token_prices():
    """Update token prices from CoinGecko"""
    try:
        call_command('update_prices')
        logger.info("✅ Price update completed successfully")
        return "Prices updated"
    except Exception as e:
        logger.error(f"❌ Price update failed: {e}")
        return f"Error: {e}"


@shared_task
def update_all_holdings_profit_loss():
    """Update profit/loss for all user holdings"""
    try:
        updated_count = 0
        errors = 0

        for holding in UserVolatilityToken.objects.select_related('token'):
            try:
                # Calculate current value
                current_price = holding.token.current_price
                holding.current_value = holding.balance * current_price

                # Calculate profit/loss
                holding.profit_loss = holding.current_value - holding.purchase_value

                if holding.purchase_value > 0:
                    holding.profit_loss_percentage = (holding.profit_loss / holding.purchase_value) * 100
                else:
                    holding.profit_loss_percentage = 0

                # Check if should auto-sell (but don't execute here, let auto-sell task handle)
                holding.save()
                updated_count += 1

            except Exception as e:
                errors += 1
                logger.error(f"Error updating holding {holding.id}: {e}")

        logger.info(f"✅ Updated profit/loss for {updated_count} holdings ({errors} errors)")
        return f"Updated {updated_count} holdings, {errors} errors"

    except Exception as e:
        logger.error(f"Failed to update holdings: {e}")
        return f"Error: {e}"


@shared_task
def check_auto_sell():
    """Check and execute auto-sell for tokens that reached 20% gain"""
    try:
        from .services.auto_sell_service import AutoSellService
        result = AutoSellService.check_and_auto_sell()
        logger.info(f"Auto-sell check completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Auto-sell check failed: {e}")
        return f"Error: {e}"


@shared_task
def check_price_alerts():
    """Check and trigger price alerts"""
    try:
        from .models import PriceAlert
        from notification.services import NotificationService

        alerts = PriceAlert.objects.filter(triggered=False).select_related('user', 'token')
        triggered_count = 0

        for alert in alerts:
            current_price = alert.token.current_price

            should_trigger = False
            if alert.alert_type == 'above' and current_price >= alert.target_price:
                should_trigger = True
            elif alert.alert_type == 'below' and current_price <= alert.target_price:
                should_trigger = True

            if should_trigger:
                alert.triggered = True
                alert.triggered_at = timezone.now()
                alert.save()

                # Send notification
                try:
                    NotificationService.send_price_alert(
                        user=alert.user,
                        token=alert.token,
                        alert_type=alert.alert_type,
                        target_price=alert.target_price,
                        current_price=current_price
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification for alert {alert.id}: {e}")

                triggered_count += 1
                logger.info(
                    f"Price alert triggered for {alert.user.username}: {alert.token.symbol} at ${current_price}")

        return {'triggered_count': triggered_count}

    except Exception as e:
        logger.error(f"Price alert check failed: {e}")
        return f"Error: {e}"


@shared_task
def distribute_yield():
    """Distribute yield to all volatility token holders"""
    try:
        holdings = UserVolatilityToken.objects.filter(balance__gt=0).select_related('user', 'token')

        total_distributed = Decimal('0')
        distributed_count = 0

        for holding in holdings:
            # Calculate daily yield (8-10% annual)
            token_value = holding.balance * holding.token.current_price
            annual_rate = Decimal(str(random.uniform(0.08, 0.10)))
            daily_rate = annual_rate / 365

            distribution_amount = token_value * daily_rate

            if distribution_amount <= 0:
                continue

            # Create yield distribution record
            distribution = YieldDistribution.objects.create(
                user_token=holding,
                amount=distribution_amount,
                percentage=annual_rate * 100,
                usd_value=distribution_amount,
                token_price=holding.token.current_price,
                distributed_at=timezone.now()
            )

            # Update user's yield balance - THIS IS IMPORTANT
            holding.vol_yield += distribution_amount  # Add to withdrawable balance
            holding.yield_earned_total += distribution_amount  # Add to total earned
            holding.save()

            total_distributed += distribution_amount
            distributed_count += 1

            logger.info(
                f"Yield distributed to {holding.user.username} for {holding.token.symbol}: ${distribution_amount:.4f}")

        logger.info(f"✅ Distributed ${total_distributed:.2f} yield to {distributed_count} holdings")

        return {'distributed_count': distributed_count, 'total_amount': float(total_distributed)}

    except Exception as e:
        logger.error(f"Yield distribution failed: {e}")
        return f"Error: {e}"


@shared_task
def distribute_hourly_yield():
    """Distribute yield hourly"""
    try:
        from .models import HourlyYield, YieldSchedule
        from datetime import datetime

        holdings = UserVolatilityToken.objects.filter(balance__gt=0).select_related('user', 'token')

        total_distributed = Decimal('0')
        distributed_count = 0
        current_day = datetime.now().day
        current_hour = timezone.now().hour

        for holding in holdings:
            # Get schedule
            try:
                schedule = YieldSchedule.objects.get(
                    user_token=holding,
                    day_of_month=current_day
                )
            except YieldSchedule.DoesNotExist:
                continue

            # Calculate hourly yield
            token_value = holding.balance * holding.token.current_price
            annual_rate = Decimal(str(random.uniform(0.08, 0.10)))
            hourly_rate = (annual_rate / 12) / 720

            distribution_amount = token_value * hourly_rate

            if distribution_amount <= 0:
                continue

            # Create hourly yield record
            hourly_yield = HourlyYield.objects.create(
                user_token=holding,
                schedule=schedule,
                hour_of_day=current_hour,
                amount=distribution_amount,
                usd_value=distribution_amount,
                token_price=holding.token.current_price,
                distributed_at=timezone.now(),
                transaction_id=f"hourly_{holding.id}_{int(timezone.now().timestamp())}"
            )

            # Update user's yield balance - THIS IS IMPORTANT
            holding.vol_yield += distribution_amount  # Add to withdrawable balance
            holding.yield_earned_total += distribution_amount  # Add to total earned
            holding.save()

            total_distributed += distribution_amount
            distributed_count += 1

            logger.info(f"Hourly yield to {holding.user.username}: ${distribution_amount:.4f}")

        logger.info(f"✅ Hourly yield: {distributed_count} holdings, Total: ${total_distributed:.4f}")

        return {'distributed_count': distributed_count, 'total_amount': float(total_distributed)}

    except Exception as e:
        logger.error(f"Hourly yield failed: {e}")
        return f"Error: {e}"



@shared_task
def withdraw_yield_to_grandbalance(user_id, amount):
    """Withdraw yield to GrandBalance for a user"""
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        amount = Decimal(str(amount))

        holdings = UserVolatilityToken.objects.filter(user=user)

        total_yield = sum(h.vol_yield for h in holdings)

        if amount > total_yield:
            return {'success': False, 'error': 'Insufficient yield balance'}

        # Withdraw from each holding proportionally
        remaining = amount
        for holding in holdings:
            if remaining <= 0:
                break

            withdrawal = min(holding.vol_yield, remaining)
            holding.vol_yield -= withdrawal
            holding.save()
            remaining -= withdrawal

        # Add to GrandBalance
        grand_balance, _ = GrandBalance.objects.get_or_create(user=user)
        grand_balance.balance_usdc += amount
        grand_balance.save()

        logger.info(f"Withdrew ${amount} yield to GrandBalance for {user.username}")

        return {'success': True, 'withdrawn': float(amount), 'new_balance': float(grand_balance.balance_usdc)}

    except Exception as e:
        logger.error(f"Yield withdrawal failed: {e}")
        return {'success': False, 'error': str(e)}

