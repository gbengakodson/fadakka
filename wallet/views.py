# wallet/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import GrandBalance  # Import your model
from django.utils import timezone


class GrandBalanceView(APIView):
    """View and manage grand balance"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get or create balance for user
            balance, created = GrandBalance.objects.get_or_create(
                user=request.user,
                defaults={
                    'balance_usdc': 0,
                    'total_deposited': 0,
                    'total_withdrawn': 0
                }
            )

            # Return ONLY fields that exist in your model
            return Response({
                'balance_usdc': float(balance.balance_usdc),
                'total_deposited': float(balance.total_deposited),
                'total_withdrawn': float(balance.total_withdrawn),
            })

        except Exception as e:
            print(f"Error in GrandBalanceView: {e}")
            return Response(
                {'error': 'Failed to fetch balance'},
                status=500
            )

    def post(self, request):
        # Handle deposit/withdrawal
        action = request.data.get('action')
        amount = request.data.get('amount', 0)

        try:
            amount = float(amount)
        except:
            return Response({'error': 'Invalid amount'}, status=400)

        balance, created = GrandBalance.objects.get_or_create(
            user=request.user,
            defaults={
                'balance_usdc': 0,
                'total_deposited': 0,
                'total_withdrawn': 0
            }
        )

        if action == 'deposit':
            balance.balance_usdc += amount
            balance.total_deposited += amount
            balance.save()
            return Response({
                'success': True,
                'new_balance': float(balance.balance_usdc)
            })
        elif action == 'withdraw':
            if amount > balance.balance_usdc:
                return Response({'error': 'Insufficient balance'}, status=400)
            balance.balance_usdc -= amount
            balance.total_withdrawn += amount
            balance.save()
            return Response({
                'success': True,
                'new_balance': float(balance.balance_usdc)
            })

        return Response({'error': 'Invalid action'}, status=400)



class BTCVolatilityWalletView(APIView):
    """View BTC volatility wallet"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # You should also replace this with real data
        # For now, let's at least make it dynamic based on actual holdings

        from volatility.models import UserVolatilityToken, VolatilityToken

        try:
            btc_token = VolatilityToken.objects.get(symbol='BTC')
            user_btc = UserVolatilityToken.objects.filter(
                user=request.user,
                token=btc_token
            ).first()

            if user_btc:
                data = {
                    'vindex_amount': float(user_btc.balance),
                    'vindex_current_value': float(user_btc.balance * btc_token.current_price),
                    'vindex_purchase_price': float(btc_token.current_price),  # You might want average purchase price
                    'vol_yield': float(user_btc.vol_yield),
                    'total_value': float(user_btc.total_value),
                    'can_sell': True,  # Add your logic here
                    'today_yield_count': 15,  # Calculate from hourly distributions
                    'yield_progress': '15/30',
                    'btc_price': float(btc_token.current_price)
                }
            else:
                # No BTC holdings
                data = {
                    'vindex_amount': 0,
                    'vindex_current_value': 0,
                    'vindex_purchase_price': 0,
                    'vol_yield': 0,
                    'total_value': 0,
                    'can_sell': False,
                    'today_yield_count': 0,
                    'yield_progress': '0/30',
                    'btc_price': float(btc_token.current_price) if btc_token else 0
                }
        except Exception as e:
            # Fallback data if something goes wrong
            data = {
                'vindex_amount': 0,
                'vindex_current_value': 0,
                'vindex_purchase_price': 0,
                'vol_yield': 0,
                'total_value': 0,
                'can_sell': False,
                'today_yield_count': 0,
                'yield_progress': '0/30',
                'btc_price': 0
            }

        return Response(data)