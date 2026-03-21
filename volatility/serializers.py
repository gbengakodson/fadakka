# volatility/serializers.py
from rest_framework import serializers
from .models import VolatilityToken, UserVolatilityToken, VolatilityOrder, YieldDistribution, PriceAlert


class VolatilityTokenSerializer(serializers.ModelSerializer):
    price_change_24h = serializers.FloatField(read_only=True)

    class Meta:
        model = VolatilityToken
        fields = ['id', 'coin_id', 'symbol', 'name', 'token_symbol',
                  'current_price', 'price_high_24h', 'price_low_24h',
                  'price_change_24h', 'monthly_yield_min', 'monthly_yield_max',
                  'created_at', 'updated_at']


class UserVolatilityTokenSerializer(serializers.ModelSerializer):
    token_symbol = serializers.CharField(source='token.token_symbol', read_only=True)
    token_name = serializers.CharField(source='token.name', read_only=True)
    current_price = serializers.DecimalField(source='token.current_price', max_digits=20, decimal_places=8,
                                             read_only=True)
    profit_loss = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    profit_loss_percentage = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_sell = serializers.BooleanField(read_only=True)
    should_auto_sell = serializers.BooleanField(read_only=True)
    total_value = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = UserVolatilityToken
        fields = ['id', 'token', 'token_symbol', 'token_name', 'balance',
                  'purchase_price', 'purchase_value', 'current_value',
                  'current_price', 'profit_loss', 'profit_loss_percentage',
                  'vol_yield', 'yield_earned_total', 'can_sell', 'should_auto_sell',
                  'total_value', 'created_at', 'updated_at']


class VolatilityOrderSerializer(serializers.ModelSerializer):
    token_symbol = serializers.CharField(source='token.token_symbol', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = VolatilityOrder
        fields = ['id', 'user', 'username', 'token', 'token_symbol', 'order_type',
                  'amount', 'price', 'total', 'node_fee', 'status', 'is_auto_sell',
                  'profit_percentage', 'created_at', 'completed_at']


class YieldDistributionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user_token.user.username', read_only=True)
    token_symbol = serializers.CharField(source='user_token.token.token_symbol', read_only=True)

    class Meta:
        model = YieldDistribution
        fields = ['id', 'user_token', 'username', 'token_symbol', 'amount',
                  'percentage', 'usd_value', 'token_price', 'distributed_at']


class PriceAlertSerializer(serializers.ModelSerializer):
    token_symbol = serializers.CharField(source='token.symbol', read_only=True)
    token_name = serializers.CharField(source='token.name', read_only=True)

    class Meta:
        model = PriceAlert
        fields = ['id', 'token', 'token_symbol', 'token_name', 'alert_type',
                  'target_price', 'triggered', 'triggered_at', 'created_at']


class PortfolioAnalyticsSerializer(serializers.Serializer):
    total_invested = serializers.FloatField()
    total_current = serializers.FloatField()
    total_profit_loss = serializers.FloatField()
    total_profit_loss_percentage = serializers.FloatField()
    total_yield_earned = serializers.FloatField()
    holdings_count = serializers.IntegerField()
    holdings = serializers.ListField(child=serializers.DictField())


class RealTimePriceSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    price = serializers.FloatField()
    change_24h = serializers.FloatField()
    market_cap = serializers.FloatField()
    volume_24h = serializers.FloatField()
    holding = serializers.DictField(required=False, allow_null=True)