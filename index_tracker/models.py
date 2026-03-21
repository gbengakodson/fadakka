# index_tracker/models.py
from django.db import models
from django.contrib.auth.models import User


# Coin model MUST come FIRST
class Coin(models.Model):
    """20 tracked cryptocurrencies"""
    SYMBOLS = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('XRP', 'XRP'),
        ('BNB', 'BNB'),
        ('SOL', 'Solana'),
        ('TRX', 'TRON'),
        ('DOGE', 'Dogecoin'),
        ('ADA', 'Cardano'),
        ('LINK', 'Chainlink'),
        ('XLM', 'Stellar'),
        ('SUI', 'Sui'),
        ('TON', 'Toncoin'),
        ('SHIB', 'Shiba Inu'),
        ('DOT', 'Polkadot'),
        ('AAVE', 'Aave'),
        ('NEAR', 'Near'),
        ('PEPE', 'Pepe'),
        ('RENDER', 'Render'),
        ('ALGO', 'Algorand'),
        ('FIL', 'Filecoin'),
    ]

    symbol = models.CharField(max_length=10, unique=True, choices=SYMBOLS)
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Current price data
    current_price_usd = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    market_cap_usd = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, default=0)

    # Price change tracking
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_change_7d = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_change_30d = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Fadakka Index calculations
    fadakka_index_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    buy_at_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    # EMA data stored as JSON for 99 weeks
    ema_history = models.JSONField(default=dict)

    # Timestamps
    last_price_update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"


# THEN define PriceHistory (depends on Coin)
class PriceHistory(models.Model):
    """Store historical prices for candlestick charts"""
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='price_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    close_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=2)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['coin', '-timestamp']),
        ]


# THEN define IndexAccess (depends on Coin and User)
class IndexAccess(models.Model):
    """Track $1 payments for viewing index prices"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='index_accesses')
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    paid_at = models.DateTimeField(auto_now_add=True)
    payment_tx_hash = models.CharField(max_length=66, blank=True, null=True)

    class Meta:
        unique_together = ['user', 'coin']

    def __str__(self):
        return f"{self.user.username} - {self.coin.symbol}"