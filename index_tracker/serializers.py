# index_tracker/serializers.py
from rest_framework import serializers
from .models import Coin

class CoinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coin
        fields = [
            'id', 'symbol', 'name', 'current_price_usd',
            'market_cap_usd', 'volume_24h', 'fadakka_index_price',
            'buy_at_price'
        ]

class PriceHistorySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    open = serializers.DecimalField(max_digits=20, decimal_places=8)
    high = serializers.DecimalField(max_digits=20, decimal_places=8)
    low = serializers.DecimalField(max_digits=20, decimal_places=8)
    close = serializers.DecimalField(max_digits=20, decimal_places=8)
    volume = serializers.DecimalField(max_digits=30, decimal_places=2)