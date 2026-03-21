# notification/services.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handle notifications for price alerts, etc."""

    @staticmethod
    def send_price_alert(user, token, alert_type, target_price, current_price):
        """Send price alert notification"""
        subject = f"Price Alert: {token.symbol} {alert_type} ${target_price}"

        message = f"""
        Hi {user.username},

        Your price alert for {token.symbol} has been triggered!

        Alert: Price is now {alert_type} ${target_price}
        Current Price: ${current_price}

        Log in to your account to view your portfolio.

        - Fadakka Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Price alert email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send price alert email: {e}")
            return False

    @staticmethod
    def send_auto_sell_notification(user, token, amount, price, profit_percentage):
        """Send notification when token is auto-sold"""
        subject = f"Auto-Sell Executed: {token.symbol} at 20% Profit!"

        message = f"""
        Hi {user.username},

        Your {token.symbol} holding has been automatically sold at a 20% profit!

        Details:
        - Token: {token.symbol}
        - Amount: {amount} tokens
        - Sold Price: ${price}
        - Profit: {profit_percentage}%

        The proceeds have been added to your GrandBalance.

        - Fadakka Team
        """

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Auto-sell notification sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send auto-sell email: {e}")
            return False