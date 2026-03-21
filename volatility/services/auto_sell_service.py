# volatility/services/auto_sell_service.py
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from ..models import UserVolatilityToken, VolatilityOrder
from wallet.models import GrandBalance
import logging

logger = logging.getLogger(__name__)


class AutoSellService:
    """Handle automatic selling of tokens that reach 20% gain"""

    @staticmethod
    @transaction.atomic
    def check_and_auto_sell():
        """Check all holdings and auto-sell those that reached 20% gain"""
        holdings = UserVolatilityToken.objects.filter(
            auto_sell_triggered=False,
            balance__gt=0
        ).select_related('user', 'token')

        sold_count = 0
        total_sold_value = Decimal('0')
        sales_by_user = {}  # Track sales per user for batch notifications

        for holding in holdings:
            # Update current value
            current_price = holding.token.current_price
            holding.update_profit_loss(current_price)

            if holding.should_auto_sell:
                logger.info(f"Auto-selling {holding.balance} {holding.token.symbol} for {holding.user.username}")

                # Calculate sale value
                sale_value = holding.balance * current_price

                # Update user's GrandBalance
                grand_balance, _ = GrandBalance.objects.get_or_create(user=holding.user)
                grand_balance.balance_usdc += sale_value
                grand_balance.save()

                # Create order record
                order = VolatilityOrder.objects.create(
                    user=holding.user,
                    token=holding.token,
                    order_type='sell',
                    amount=holding.balance,
                    price=current_price,
                    total=sale_value,
                    node_fee=Decimal('0'),  # No node fee on auto-sells
                    status='completed',
                    completed_at=timezone.now(),
                    is_auto_sell=True,
                    profit_percentage=holding.profit_loss_percentage
                )

                # Track for batch notification
                user_id = holding.user.id
                if user_id not in sales_by_user:
                    sales_by_user[user_id] = {
                        'user': holding.user,
                        'sales': [],
                        'total_profit': Decimal('0')
                    }

                sales_by_user[user_id]['sales'].append({
                    'token': holding.token.symbol,
                    'amount': holding.balance,
                    'price': current_price,
                    'profit': holding.profit_loss_percentage,
                    'profit_amount': holding.profit_loss
                })
                sales_by_user[user_id]['total_profit'] += holding.profit_loss_percentage

                # Mark as auto-sold
                holding.auto_sell_triggered = True
                holding.save()

                # Optional: Don't delete holding, keep for history
                # You might want to keep or set balance to 0
                # holding.balance = 0
                # holding.save()

                sold_count += 1
                total_sold_value += sale_value

        # Send batch notifications
        for user_data in sales_by_user.values():
            AutoSellService._send_batch_notification(
                user_data['user'],
                user_data['sales'],
                user_data['total_profit']
            )

        if sold_count > 0:
            logger.info(f"Auto-sold {sold_count} holdings totaling ${total_sold_value}")

        return {
            'sold_count': sold_count,
            'total_value': float(total_sold_value),
            'sales_by_user': len(sales_by_user)
        }

    @staticmethod
    def _send_batch_notification(user, sales, total_profit):
        """Send batch notification for multiple auto-sales"""
        try:
            subject = f"🎉 Auto-Sell Batch: {len(sales)} Tokens Sold at 20% Profit!"

            # Build sales HTML
            sales_html = ""
            for sale in sales:
                sales_html += f"""
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px;"><strong>{sale['token']}</strong></td>
                    <td style="padding: 10px;">{sale['amount']:.8f}</td>
                    <td style="padding: 10px;">${sale['price']:.2f}</td>
                    <td style="padding: 10px; color: #10b981;">+{sale['profit']:.2f}%</td>
                    <td style="padding: 10px; color: #10b981;">+${sale['profit_amount']:.2f}</td>
                </tr>
                """

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                        line-height: 1.6;
                        color: #1a1a2e;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: #ffffff;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        color: white;
                        margin: 0;
                        font-size: 28px;
                    }}
                    .header p {{
                        color: rgba(255, 255, 255, 0.9);
                        margin: 10px 0 0;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .greeting {{
                        font-size: 18px;
                        margin-bottom: 20px;
                    }}
                    .greeting strong {{
                        color: #10b981;
                    }}
                    .sales-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        background: #f8fafc;
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    .sales-table th {{
                        background: #e2e8f0;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                        color: #1e293b;
                    }}
                    .sales-table td {{
                        padding: 12px;
                        border-bottom: 1px solid #e2e8f0;
                    }}
                    .total-profit {{
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        padding: 20px;
                        border-radius: 8px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .total-profit span {{
                        color: white;
                        font-size: 14px;
                        display: block;
                    }}
                    .total-profit .amount {{
                        font-size: 32px;
                        font-weight: bold;
                        color: white;
                        margin-top: 5px;
                    }}
                    .button {{
                        display: inline-block;
                        background: #2563eb;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 8px;
                        margin-top: 20px;
                        font-weight: 500;
                    }}
                    .footer {{
                        background: #f8fafc;
                        padding: 20px;
                        text-align: center;
                        color: #64748b;
                        font-size: 12px;
                        border-top: 1px solid #e2e8f0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Auto-Sell Executed!</h1>
                        <p>Your tokens were automatically sold at 20% profit</p>
                    </div>

                    <div class="content">
                        <div class="greeting">
                            Hi <strong>{user.username}</strong>,
                        </div>

                        <p>Great news! {len(sales)} of your holdings have reached the 20% profit target and were automatically sold.</p>

                        <table class="sales-table">
                            <thead>
                                <tr>
                                    <th>Token</th>
                                    <th>Amount</th>
                                    <th>Sell Price</th>
                                    <th>Profit %</th>
                                    <th>Profit</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sales_html}
                            </tbody>
                        </table>

                        <div class="total-profit">
                            <span>Total Profit Earned</span>
                            <div class="amount">+{total_profit:.2f}%</div>
                        </div>

                        <p>The proceeds have been added to your GrandBalance and are ready for trading!</p>

                        <div style="text-align: center;">
                            <a href="https://yourdomain.com/dashboard" class="button">View Your Dashboard</a>
                        </div>
                    </div>

                    <div class="footer">
                        <p>This is an automated message from Fadakka.</p>
                        <p>If you have any questions, please contact our support team.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            🎉 Auto-Sell Batch: {len(sales)} Tokens Sold at 20% Profit!

            Hi {user.username},

            Great news! {len(sales)} of your holdings have reached the 20% profit target and were automatically sold.

            Sales Summary:
            """

            for sale in sales:
                plain_message += f"""
            - {sale['token']}: {sale['amount']:.8f} tokens @ ${sale['price']:.2f} (Profit: +{sale['profit']:.2f}%)
            """

            plain_message += f"""

            Total Profit: +{total_profit:.2f}%

            The proceeds have been added to your GrandBalance.

            View your dashboard: https://yourdomain.com/dashboard

            - Fadakka Team
            """

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Auto-sell batch notification sent to {user.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send auto-sell batch email: {e}")
            return False

    @staticmethod
    def check_single_holding(holding):
        """Check and auto-sell a single holding (for testing)"""
        current_price = holding.token.current_price
        holding.update_profit_loss(current_price)

        if holding.should_auto_sell:
            return AutoSellService._execute_auto_sell(holding)

        return {'auto_sold': False, 'reason': 'Not reached 20% gain'}

    @staticmethod
    def _execute_auto_sell(holding):
        """Execute auto-sell for a single holding"""
        try:
            with transaction.atomic():
                current_price = holding.token.current_price
                sale_value = holding.balance * current_price

                # Update GrandBalance
                grand_balance, _ = GrandBalance.objects.get_or_create(user=holding.user)
                grand_balance.balance_usdc += sale_value
                grand_balance.save()

                # Create order
                order = VolatilityOrder.objects.create(
                    user=holding.user,
                    token=holding.token,
                    order_type='sell',
                    amount=holding.balance,
                    price=current_price,
                    total=sale_value,
                    node_fee=Decimal('0'),
                    status='completed',
                    completed_at=timezone.now(),
                    is_auto_sell=True,
                    profit_percentage=holding.profit_loss_percentage
                )

                # Mark as auto-sold
                holding.auto_sell_triggered = True
                holding.save()

                # Send notification
                AutoSellService._send_single_notification(
                    holding.user,
                    holding.token,
                    holding.balance,
                    current_price,
                    holding.profit_loss_percentage
                )

                return {
                    'auto_sold': True,
                    'order_id': order.id,
                    'sale_value': float(sale_value),
                    'profit_percentage': float(holding.profit_loss_percentage)
                }

        except Exception as e:
            logger.error(f"Auto-sell failed for {holding.user.username}: {e}")
            return {'auto_sold': False, 'error': str(e)}

    @staticmethod
    def _send_single_notification(user, token, amount, price, profit_percentage):
        """Send single notification for auto-sell"""
        try:
            subject = f"🎉 Auto-Sell Executed: {token.symbol} at 20% Profit!"

            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; }}
                    .header h1 {{ color: white; margin: 0; }}
                    .content {{ padding: 30px; }}
                    .details {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Auto-Sell Executed!</h1>
                    </div>
                    <div class="content">
                        <p>Hi <strong>{user.username}</strong>,</p>
                        <p>Your <strong>{token.symbol}</strong> holding has reached 20% profit and was automatically sold!</p>
                        <div class="details">
                            <p><strong>Token:</strong> {token.name} ({token.symbol})</p>
                            <p><strong>Amount:</strong> {amount:.8f} tokens</p>
                            <p><strong>Sell Price:</strong> ${price:.2f}</p>
                            <p><strong>Profit:</strong> +{profit_percentage:.2f}%</p>
                        </div>
                        <p>Proceeds have been added to your GrandBalance.</p>
                        <div style="text-align: center;">
                            <a href="https://yourdomain.com/dashboard" class="button">View Dashboard</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            Auto-Sell Executed: {token.symbol} at 20% Profit!

            Your {token.symbol} holding was automatically sold.

            Amount: {amount:.8f} tokens
            Sell Price: ${price:.2f}
            Profit: +{profit_percentage:.2f}%

            Proceeds added to your GrandBalance.
            """

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send auto-sell notification: {e}")
            return False