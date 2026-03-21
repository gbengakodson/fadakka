# wallet/services/notification_service.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Handle email notifications for transactions"""

    @staticmethod
    def send_deposit_confirmation(user, amount, tx_hash, new_balance):
        """Send deposit confirmation email"""
        subject = f'Deposit Confirmed - ${amount} USDC'

        html_message = render_to_string('emails/deposit_confirmation.html', {
            'user': user,
            'amount': amount,
            'tx_hash': tx_hash,
            'new_balance': new_balance,
            'date': timezone.now().strftime('%B %d, %Y %H:%M')
        })

        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Deposit confirmation email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send deposit email: {e}")
            return False

    @staticmethod
    def send_withdrawal_confirmation(user, amount, to_address, new_balance, status='pending'):
        """Send withdrawal confirmation email"""
        subject = f'Withdrawal {"Confirmed" if status == "completed" else "Pending"} - ${amount} USDC'

        html_message = render_to_string('emails/withdrawal_confirmation.html', {
            'user': user,
            'amount': amount,
            'to_address': to_address,
            'new_balance': new_balance,
            'status': status,
            'date': timezone.now().strftime('%B %d, %Y %H:%M')
        })

        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Withdrawal email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send withdrawal email: {e}")
            return False

    @staticmethod
    def send_kyc_verification_email(user, status='pending'):
        """Send KYC verification status email"""
        subject = f'KYC Verification {status.title()}'

        html_message = render_to_string('emails/kyc_verification.html', {
            'user': user,
            'status': status,
            'date': timezone.now().strftime('%B %d, %Y %H:%M')
        })

        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"KYC email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send KYC email: {e}")
            return False