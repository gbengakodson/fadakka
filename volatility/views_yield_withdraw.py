from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from .models import UserVolatilityToken
from wallet.models import GrandBalance


class WithdrawYieldView(APIView):
    """Withdraw yield earnings to GrandBalance"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token_id = request.data.get('token_id')
        amount = request.data.get('amount')

        if not token_id or not amount:
            return Response(
                {'error': 'Token ID and amount required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response(
                    {'error': 'Amount must be positive'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except:
            return Response(
                {'error': 'Invalid amount'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_token = UserVolatilityToken.objects.get(
                user=request.user,
                token_id=token_id
            )
        except UserVolatilityToken.DoesNotExist:
            return Response(
                {'error': 'Token not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has enough yield
        if user_token.vol_yield < amount:
            return Response({
                'error': 'Insufficient yield balance',
                'available': float(user_token.vol_yield)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get current price for USD value
        usd_value = amount * user_token.token.current_price

        # Withdraw yield
        user_token.vol_yield -= amount
        user_token.save()

        # Add to GrandBalance
        grand_balance, _ = GrandBalance.objects.get_or_create(user=request.user)
        grand_balance.balance_usdc += float(usd_value)
        grand_balance.save()

        return Response({
            'success': True,
            'message': f'Withdrew {amount} yield (${usd_value:.2f}) to GrandBalance',
            'new_yield_balance': float(user_token.vol_yield),
            'new_grand_balance': float(grand_balance.balance_usdc)
        })


class YieldBalanceView(APIView):
    """Get yield balances for all tokens"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_tokens = UserVolatilityToken.objects.filter(user=request.user)

        data = []
        total_yield_usd = 0

        for token in user_tokens:
            usd_value = float(token.vol_yield) * float(token.token.current_price)
            total_yield_usd += usd_value

            data.append({
                'token_id': token.token.id,
                'token_symbol': token.token.token_symbol,
                'token_name': token.token.name,
                'principal': float(token.balance),
                'yield_amount': float(token.vol_yield),
                'yield_usd': usd_value,
                'current_price': float(token.token.current_price),
                'can_withdraw': token.vol_yield > 0
            })

        return Response({
            'tokens': data,
            'total_yield_usd': total_yield_usd
        })