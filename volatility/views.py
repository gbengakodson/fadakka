from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from .models import VolatilityToken, UserVolatilityToken, VolatilityOrder, YieldDistribution, PriceAlert, HourlyYield
from .serializers import (
    VolatilityTokenSerializer,
    UserVolatilityTokenSerializer,
    VolatilityOrderSerializer,
    PriceAlertSerializer,
    PortfolioAnalyticsSerializer,
    RealTimePriceSerializer
)

from wallet.models import GrandBalance
from referral.models import ReferralNode, NodeFeeDistribution, ReferralStats
from .services.price_service import PriceService


class VolatilityTokenListView(generics.ListAPIView):
    """List all available volatility tokens"""
    queryset = VolatilityToken.objects.all()
    serializer_class = VolatilityTokenSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserVolatilityTokensView(generics.ListAPIView):
    """Get user's volatility token holdings"""
    serializer_class = UserVolatilityTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserVolatilityToken.objects.filter(user=self.request.user)


class BuyVolatilityTokenView(APIView):
    """Handle buying volatility tokens with proper balance validation and referral distribution"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            print("🔵 Buy request received")

            # Get and validate input parameters
            token_id = request.data.get('token_id')

            try:
                amount = Decimal(str(request.data.get('amount', 0)))
                price = Decimal(str(request.data.get('price', 0)))
                print(f"🔵 Amount: {amount}, Price: {price}")
            except Exception as e:
                print(f"🔴 Error parsing amount/price: {e}")
                return Response(
                    {'error': 'Invalid amount or price format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate inputs
            if not token_id:
                return Response(
                    {'error': 'Token ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if amount <= 0:
                return Response(
                    {'error': 'Amount must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if price <= 0:
                return Response(
                    {'error': 'Price must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get the token
            try:
                token = VolatilityToken.objects.get(id=token_id)
                print(f"🔵 Token found: {token.token_symbol}")
            except VolatilityToken.DoesNotExist:
                return Response(
                    {'error': 'Token not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calculate total cost
            total_cost = amount * price
            print(f"🔵 Total cost: {total_cost}")

            # Calculate node fee (10%)
            node_fee = total_cost * Decimal('0.10')
            print(f"🔵 Node fee: {node_fee}")

            # Get user's GrandBalance with select_for_update
            try:
                balance = GrandBalance.objects.select_for_update().get(user=request.user)
                print(f"🔵 Balance found: {balance.balance_usdc}")
            except GrandBalance.DoesNotExist:
                print(f"🔵 Creating new balance for user")
                balance = GrandBalance.objects.create(
                    user=request.user,
                    balance_usdc=0,
                    total_deposited=0,
                    total_withdrawn=0
                )

            # Check balance
            if balance.balance_usdc < total_cost:
                return Response(
                    {
                        'error': 'Insufficient GrandBalance',
                        'required': float(total_cost),
                        'available': float(balance.balance_usdc)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create order record
            order = VolatilityOrder.objects.create(
                user=request.user,
                token=token,
                order_type='buy',
                amount=amount,
                price=price,
                total=total_cost,
                node_fee=node_fee,
                status='completed',
                completed_at=timezone.now()
            )
            print(f"🔵 Order created: {order.id}")

            # Deduct from GrandBalance
            balance.balance_usdc -= total_cost
            balance.save()
            print(f"🔵 Balance updated: {balance.balance_usdc}")

            # Get or create user's token holdings
            user_token, created = UserVolatilityToken.objects.select_for_update().get_or_create(
                user=request.user,
                token=token,
                defaults={
                    'balance': amount,
                    'purchase_price': price,
                    'purchase_value': amount * price,
                    'current_value': amount * price,
                    'profit_loss': 0,
                    'profit_loss_percentage': 0,
                    'vol_yield': 0,
                    'yield_earned_total': 0,
                    'auto_sell_triggered': False,
                    'highest_price_seen': price
                }
            )
            print(f"🔵 User token - Created: {created}, Balance: {user_token.balance}")

            # If token already existed, update average purchase price
            if not created:
                try:
                    # Calculate new average purchase price
                    old_total_value = user_token.balance * user_token.purchase_price
                    new_total_value = old_total_value + (amount * price)
                    new_total_balance = user_token.balance + amount

                    print(f"🔵 Old total value: {old_total_value}")
                    print(f"🔵 New total value: {new_total_value}")
                    print(f"🔵 New total balance: {new_total_balance}")

                    if new_total_balance > 0:
                        user_token.purchase_price = new_total_value / new_total_balance
                        user_token.purchase_value = new_total_value
                    else:
                        user_token.purchase_price = price
                        user_token.purchase_value = amount * price

                    user_token.balance = new_total_balance
                    user_token.current_value = user_token.balance * token.current_price
                    user_token.profit_loss = user_token.current_value - user_token.purchase_value

                    if user_token.purchase_value > 0:
                        user_token.profit_loss_percentage = (user_token.profit_loss / user_token.purchase_value) * 100
                    else:
                        user_token.profit_loss_percentage = 0

                    # Update highest price seen
                    if token.current_price > user_token.highest_price_seen:
                        user_token.highest_price_seen = token.current_price

                    user_token.save()
                    print(f"🔵 User token updated successfully")
                except Exception as e:
                    print(f"🔴 Error updating existing token: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

            # Process referral node fees
            self.distribute_node_fees(request.user, node_fee, order)

            # Serialize the order for response
            serializer = VolatilityOrderSerializer(order)

            return Response({
                'success': True,
                'message': f'Successfully bought {amount} {token.token_symbol}',
                'order': serializer.data,
                'new_balance': float(balance.balance_usdc),
                'token_balance': float(user_token.balance),
                'token_symbol': token.token_symbol,
                'node_fee_paid': float(node_fee)
            })

        except Exception as e:
            print(f"🔴 Unhandled error in buy view: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def distribute_node_fees(self, user, node_fee, order):
        """Distribute node fees through the 7-generation referral tree"""
        current_user = user
        commission_rates = {
            1: 1.00,  # 100%
            2: 0.20,  # 20%
            3: 0.10,  # 10%
            4: 0.07,  # 7%
            5: 0.05,  # 5%
            6: 0.03,  # 3%
            7: 0.01  # 1%
        }

        # Keep track to avoid cycles
        processed_users = set()

        for level in range(1, 8):
            try:
                # Get the referrer for current user
                referral_node = ReferralNode.objects.get(user=current_user)

                if not referral_node.referrer or referral_node.referrer.id in processed_users:
                    break

                referrer = referral_node.referrer
                processed_users.add(referrer.id)

                commission_rate = commission_rates[level]
                commission_amount = node_fee * Decimal(str(commission_rate))

                if commission_amount > 0:
                    # Create distribution record
                    NodeFeeDistribution.objects.create(
                        from_user=user,
                        to_user=referrer,
                        amount=commission_amount,
                        level=level,
                        purchase=order,
                        node_fee_total=node_fee,
                        commission_percentage=commission_rate * 100
                    )

                    # Add to referrer's grand balance
                    referrer_balance, _ = GrandBalance.objects.get_or_create(user=referrer)
                    referrer_balance.balance_usdc += commission_amount
                    referrer_balance.save()

                    # Update referrer's total earned in ReferralNode
                    referrer_node = ReferralNode.objects.get(user=referrer)
                    referrer_node.total_earned += commission_amount
                    referrer_node.save()

                    # Update referral stats
                    self.update_referrer_stats(referrer, level, commission_amount)

                    # Update the level_* JSON fields in referrer's node
                    self.update_referral_levels(referrer_node, user.id, level)

                # Move up the chain for next level
                current_user = referrer

            except ReferralNode.DoesNotExist:
                break

    def update_referrer_stats(self, referrer, level, amount):
        """Update referral statistics for a referrer"""
        stats, created = ReferralStats.objects.get_or_create(user=referrer)

        # Update level count
        level_count_attr = f'level_{level}_count'
        if hasattr(stats, level_count_attr):
            current_count = getattr(stats, level_count_attr)
            setattr(stats, level_count_attr, current_count + 1)

        # Update level earnings
        level_earnings_attr = f'level_{level}_earnings'
        if hasattr(stats, level_earnings_attr):
            current_earnings = getattr(stats, level_earnings_attr)
            setattr(stats, level_earnings_attr, current_earnings + amount)

        # Update totals
        stats.total_earned += amount
        stats.total_referrals += 1

        # Check if this makes them active (first purchase)
        if not NodeFeeDistribution.objects.filter(
                from_user=referrer,
                to_user=referrer
        ).exists():
            stats.active_referrals += 1

        stats.save()

    def update_referral_levels(self, referrer_node, downline_user_id, level):
        """Update the JSON fields tracking downlines at each level"""
        level_field = f'level_{level}'

        if hasattr(referrer_node, level_field):
            current_list = getattr(referrer_node, level_field)

            # Add user if not already in the list
            if downline_user_id not in current_list:
                current_list.append(downline_user_id)

                # Keep only the most recent 100 to prevent huge JSON
                if len(current_list) > 100:
                    current_list = current_list[-100:]

                setattr(referrer_node, level_field, current_list)
                referrer_node.save()


class SellVolatilityTokenView(APIView):
    """Handle selling volatility tokens with proper balance validation"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Get and validate input parameters
        token_id = request.data.get('token_id')

        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            price = Decimal(str(request.data.get('price', 0)))
        except:
            return Response(
                {'error': 'Invalid amount or price format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate inputs
        if not token_id:
            return Response(
                {'error': 'Token ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {'error': 'Amount must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if price <= 0:
            return Response(
                {'error': 'Price must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the token
        try:
            token = VolatilityToken.objects.get(id=token_id)
        except VolatilityToken.DoesNotExist:
            return Response(
                {'error': 'Token not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check user's token balance with select_for_update
        try:
            user_token = UserVolatilityToken.objects.select_for_update().get(
                user=request.user,
                token=token
            )
        except UserVolatilityToken.DoesNotExist:
            return Response(
                {
                    'error': 'You don\'t own this token',
                    'token_symbol': token.token_symbol,
                    'available': 0
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if can sell (price >= purchase price)
        if price < user_token.purchase_price:
            return Response(
                {
                    'error': f'Cannot sell. Current price (${price}) is below purchase price (${user_token.purchase_price})',
                    'purchase_price': float(user_token.purchase_price),
                    'current_price': float(price)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # SERVER-SIDE TOKEN BALANCE CHECK
        if user_token.balance < amount:
            return Response(
                {
                    'error': 'Insufficient token balance',
                    'required': float(amount),
                    'available': float(user_token.balance),
                    'token_symbol': token.token_symbol
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total value
        total_value = amount * price

        # Get GrandBalance with select_for_update
        try:
            balance = GrandBalance.objects.select_for_update().get(user=request.user)
        except GrandBalance.DoesNotExist:
            return Response(
                {'error': 'GrandBalance not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create order record
        order = VolatilityOrder.objects.create(
            user=request.user,
            token=token,
            order_type='sell',
            amount=amount,
            price=price,
            total=total_value,
            status='completed',
            completed_at=timezone.now()
        )

        # Add to GrandBalance
        balance.balance_usdc += total_value
        balance.save()

        # Deduct from user's token holdings
        user_token.balance -= amount

        # Update profit/loss after sale
        if user_token.balance > 0:
            user_token.current_value = user_token.balance * token.current_price
            user_token.profit_loss = user_token.current_value - user_token.purchase_value
            if user_token.purchase_value > 0:
                user_token.profit_loss_percentage = (user_token.profit_loss / user_token.purchase_value) * 100
        else:
            user_token.current_value = 0
            user_token.profit_loss = 0
            user_token.profit_loss_percentage = 0

        user_token.save()

        # Serialize the order for response
        serializer = VolatilityOrderSerializer(order)

        return Response({
            'success': True,
            'message': f'Successfully sold {amount} {token.token_symbol}',
            'order': serializer.data,
            'new_balance': float(balance.balance_usdc),
            'token_balance': float(user_token.balance),
            'token_symbol': token.token_symbol
        })


class UserOrderHistoryView(generics.ListAPIView):
    """Get user's order history"""
    serializer_class = VolatilityOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VolatilityOrder.objects.filter(user=self.request.user).order_by('-created_at')


class RealTimePricesView(APIView):
    """Get real-time prices for all tokens"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        prices = PriceService.get_all_prices()

        if not prices:
            return Response({'error': 'Failed to fetch prices'}, status=500)

        # Get user's holdings for profit/loss calculation
        holdings = UserVolatilityToken.objects.filter(user=request.user)
        holdings_dict = {h.token.coin_id: h for h in holdings}

        data = {}
        for token in VolatilityToken.objects.all():
            coin_data = prices.get(token.coin_id, {})
            holding = holdings_dict.get(token.coin_id)

            data[token.symbol] = {
                'price': float(coin_data.get('usd', 0)),
                'change_24h': float(coin_data.get('usd_24h_change', 0)),
                'market_cap': float(coin_data.get('usd_market_cap', 0)),
                'volume_24h': float(coin_data.get('usd_24h_vol', 0)),
                'holding': {
                    'balance': float(holding.balance) if holding else 0,
                    'purchase_price': float(holding.purchase_price) if holding else 0,
                    'profit_loss': float(holding.profit_loss) if holding else 0,
                    'profit_loss_percentage': float(holding.profit_loss_percentage) if holding else 0,
                    'can_sell': holding.can_sell if holding else False
                } if holding else None
            }

        return Response(data)


class PriceAlertView(APIView):
    """Manage price alerts"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user)
        serializer = PriceAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    def post(self, request):
        token_id = request.data.get('token_id')
        alert_type = request.data.get('alert_type')
        target_price = request.data.get('target_price')

        if not all([token_id, alert_type, target_price]):
            return Response({'error': 'Missing required fields'}, status=400)

        try:
            token = VolatilityToken.objects.get(id=token_id)
            target_price = Decimal(str(target_price))
        except VolatilityToken.DoesNotExist:
            return Response({'error': 'Token not found'}, status=404)
        except:
            return Response({'error': 'Invalid target price'}, status=400)

        # Check if alert already exists
        existing = PriceAlert.objects.filter(
            user=request.user,
            token=token,
            alert_type=alert_type,
            triggered=False
        ).first()

        if existing:
            return Response({'error': 'Alert already exists'}, status=400)

        alert = PriceAlert.objects.create(
            user=request.user,
            token=token,
            alert_type=alert_type,
            target_price=target_price
        )

        serializer = PriceAlertSerializer(alert)
        return Response(serializer.data, status=201)

    def delete(self, request, alert_id):
        try:
            alert = PriceAlert.objects.get(id=alert_id, user=request.user)
            alert.delete()
            return Response({'success': True})
        except PriceAlert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=404)


class PortfolioAnalyticsView(APIView):
    """Get portfolio analytics with profit/loss"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        holdings = UserVolatilityToken.objects.filter(user=request.user)

        total_invested = sum(float(h.purchase_value) for h in holdings)
        total_current = sum(float(h.current_value) for h in holdings)
        total_profit_loss = total_current - total_invested
        total_profit_loss_percentage = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0

        # Get yield earned
        total_yield = sum(float(h.yield_earned_total) for h in holdings)

        # Get holdings breakdown
        holdings_data = []
        for holding in holdings:
            holdings_data.append({
                'id': holding.id,
                'token': holding.token.symbol,
                'token_name': holding.token.name,
                'balance': float(holding.balance),
                'purchase_price': float(holding.purchase_price),
                'current_price': float(holding.token.current_price),
                'current_value': float(holding.current_value),
                'profit_loss': float(holding.profit_loss),
                'profit_loss_percentage': float(holding.profit_loss_percentage),
                'can_sell': holding.can_sell,
                'yield_earned': float(holding.yield_earned_total),
                'auto_sell_pending': holding.profit_loss_percentage >= 20
            })

        return Response({
            'total_invested': total_invested,
            'total_current': total_current,
            'total_profit_loss': total_profit_loss,
            'total_profit_loss_percentage': total_profit_loss_percentage,
            'total_yield_earned': total_yield,
            'holdings': holdings_data,
            'holdings_count': len(holdings)
        })


class WithdrawYieldView(APIView):
    """Withdraw yield to GrandBalance"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        print(f"Withdrawal request for {user.username}")

        try:
            # Get all holdings for this user
            holdings = UserVolatilityToken.objects.filter(user=user)

            # Calculate total yield
            total_yield = sum(h.vol_yield for h in holdings)

            print(f"Total yield available: {total_yield}")

            if total_yield <= 0:
                return Response({'error': 'No yield to withdraw'}, status=400)

            # Add to GrandBalance
            balance, _ = GrandBalance.objects.get_or_create(user=user)
            balance.balance_usdc += total_yield
            balance.save()

            # Reset yields
            for holding in holdings:
                holding.vol_yield = 0
                holding.save()

            return Response({
                'success': True,
                'message': f'Successfully withdrew ${total_yield:.6f}',
                'withdrawn': float(total_yield),
                'new_balance': float(balance.balance_usdc)
            })

        except Exception as e:
            print(f"Error in withdraw: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class YieldDistributionsView(APIView):
    """Get user's yield distributions"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            # Simple version - just get hourly yields
            hourly = HourlyYield.objects.filter(
                user_token__user=user
            ).order_by('-distributed_at')[:20]

            distributions = []

            for h in hourly:
                distributions.append({
                    'id': h.id,
                    'type': 'hourly',
                    'amount': float(h.amount),
                    'token': h.user_token.token.symbol,
                    'date': h.distributed_at.isoformat(),
                    'hour': h.hour_of_day
                })

            return Response(distributions)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)




class YieldStatsView(APIView):
    """Get yield statistics"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            holdings = UserVolatilityToken.objects.filter(user=user)

            total_yield_earned = sum(h.yield_earned_total for h in holdings)
            current_portfolio_value = sum(h.current_value for h in holdings)

            # Use Decimal for calculations
            min_yield = current_portfolio_value * Decimal('0.08')
            max_yield = current_portfolio_value * Decimal('0.10')

            return Response({
                'total_yield_earned': float(total_yield_earned),
                'current_value': float(current_portfolio_value),
                'projected_annual_yield': {
                    'min': float(min_yield),
                    'max': float(max_yield)
                }
            })
        except Exception as e:
            print(f"Error in YieldStatsView: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class YieldHourlyView(APIView):
    """Get hourly yield distributions"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 24))

            # Get from YieldDistribution (since HourlyYield might not have data)
            hourly = YieldDistribution.objects.filter(
                user_token__user=user
            ).order_by('-distributed_at')[:limit]

            data = []
            for h in hourly:
                data.append({
                    'id': h.id,
                    'amount': float(h.amount),
                    'usd_value': float(h.usd_value),
                    'token': h.user_token.token.symbol,
                    'date': h.distributed_at.isoformat()
                })

            return Response(data)
        except Exception as e:
            print(f"Error in YieldHourlyView: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class YieldDailyView(APIView):
    """Get daily yield distributions"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 30))

            daily = YieldDistribution.objects.filter(
                user_token__user=user
            ).order_by('-distributed_at')[:limit]

            data = []
            for d in daily:
                data.append({
                    'id': d.id,
                    'amount': float(d.amount),
                    'usd_value': float(d.usd_value),
                    'token': d.user_token.token.symbol,
                    'percentage': float(d.percentage),
                    'date': d.distributed_at.isoformat()
                })

            return Response(data)
        except Exception as e:
            print(f"Error in YieldDailyView: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class YieldBalanceView(APIView):
    """Get yield balance per token"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            holdings = UserVolatilityToken.objects.filter(user=user)

            data = []
            for h in holdings:
                data.append({
                    'token_id': h.token.id,
                    'token_symbol': h.token.symbol,
                    'token_name': h.token.name,
                    'yield_balance': float(h.vol_yield),
                    'yield_earned_total': float(h.yield_earned_total),
                    'current_value': float(h.current_value)
                })

            return Response(data)
        except Exception as e:
            print(f"Error in YieldBalanceView: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)