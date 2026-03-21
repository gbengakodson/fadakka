from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class VolatilityToken(models.Model):
    """Represents a volatility token for a specific coin"""
    coin_id = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    token_symbol = models.CharField(max_length=20)

    # Current price (linked to underlying coin price)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # Price tracking
    price_high_24h = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price_low_24h = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Yield parameters
    monthly_yield_min = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    monthly_yield_max = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)

    # Price alert subscribers (JSON list of user IDs)
    price_alert_subscribers = models.JSONField(default=list, blank=True)
    alert_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Volatility Token"
        verbose_name_plural = "Volatility Tokens"

    def __str__(self):
        return self.token_symbol

    @property
    def price_change_percentage(self):
        """Calculate 24h price change percentage"""
        if self.price_low_24h > 0:
            return ((self.current_price - self.price_low_24h) / self.price_low_24h) * 100
        return 0


class UserVolatilityToken(models.Model):
    """Tracks user's holdings of volatility tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volatility_tokens')
    token = models.ForeignKey(VolatilityToken, on_delete=models.CASCADE)

    # Investment details
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    purchase_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    purchase_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # Profit tracking
    profit_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    profit_loss_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Yield earned
    vol_yield = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    yield_earned_total = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    # Auto-sell tracking
    auto_sell_triggered = models.BooleanField(default=False)
    highest_price_seen = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    last_yield_calculation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'token']

    def __str__(self):
        return f"{self.user.username} - {self.token.token_symbol}: {self.balance} (P/L: {self.profit_loss_percentage}%)"

    def update_profit_loss(self, current_price):
        """Update profit/loss based on current price"""
        self.current_value = self.balance * current_price
        self.profit_loss = self.current_value - self.purchase_value
        self.profit_loss_percentage = (self.profit_loss / self.purchase_value) * 100 if self.purchase_value > 0 else 0
        self.save()

        # Track highest price for auto-sell
        if current_price > self.highest_price_seen:
            self.highest_price_seen = current_price
            self.save()

        return self.profit_loss_percentage

    @property
    def can_sell(self):
        """Check if user can sell based on current price"""
        return self.token.current_price >= self.purchase_price

    @property
    def should_auto_sell(self):
        """Check if token has reached 20% gain and should auto-sell"""
        if self.auto_sell_triggered:
            return False
        return self.profit_loss_percentage >= 20

    @property
    def total_value(self):
        return self.current_value + (self.vol_yield * self.token.current_price)


class VolatilityOrder(models.Model):
    """Track buy/sell orders for volatility tokens"""
    ORDER_TYPES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='volatility_orders')
    token = models.ForeignKey(VolatilityToken, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)

    # Order details
    amount = models.DecimalField(max_digits=20, decimal_places=8)  # Number of tokens
    price = models.DecimalField(max_digits=20, decimal_places=8)  # Price per token in USDC
    total = models.DecimalField(max_digits=20, decimal_places=8)  # amount * price

    # Add this field - Node fee (10% of total)
    node_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="10% node fee deducted from purchase"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    is_auto_sell = models.BooleanField(default=False, help_text="Was this an automatic 20% profit sell?")
    profit_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.order_type} {self.amount} {self.token.token_symbol} @ ${self.price}"



    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.order_type} {self.amount} {self.token.token_symbol} @ ${self.price}"



class YieldDistribution(models.Model):
    """Track monthly yield distributions"""
    user_token = models.ForeignKey(UserVolatilityToken, on_delete=models.CASCADE, related_name='yield_distributions')
    amount = models.DecimalField(max_digits=20, decimal_places=8)  # Yield amount in tokens
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Yield percentage for this distribution
    usd_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)  # USD value at distribution time
    token_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)  # Token price at distribution
    distributed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-distributed_at']

    def __str__(self):
        return f"{self.user_token.user.username} - {self.amount} tokens (${self.usd_value}) - {self.distributed_at.date()}"


class YieldSchedule(models.Model):
    """Track daily yield schedule for each user"""
    user_token = models.ForeignKey(UserVolatilityToken, on_delete=models.CASCADE, related_name='yield_schedules')
    day_of_month = models.IntegerField()  # 1-30
    expected_amount = models.DecimalField(max_digits=20, decimal_places=8)
    distributed_amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('partial', 'Partially Distributed'),
        ('completed', 'Completed')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user_token', 'day_of_month']
        ordering = ['day_of_month']

    def __str__(self):
        return f"{self.user_token.user.username} - Day {self.day_of_month}: {self.expected_amount}"


class HourlyYield(models.Model):
    """Track each hourly yield distribution"""
    user_token = models.ForeignKey(UserVolatilityToken, on_delete=models.CASCADE, related_name='hourly_yields')
    schedule = models.ForeignKey(YieldSchedule, on_delete=models.CASCADE, related_name='hourly_distributions')
    hour_of_day = models.IntegerField()  # 0-23
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    usd_value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    token_price = models.DecimalField(max_digits=20, decimal_places=8)
    distributed_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        ordering = ['-distributed_at']

    def __str__(self):
        return f"{self.user_token.user.username} - Hour {self.hour_of_day}: ${self.usd_value}"


class PriceAlert(models.Model):
    """Track price alerts for users"""
    ALERT_TYPES = (
        ('above', 'Price Above'),
        ('below', 'Price Below'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    token = models.ForeignKey(VolatilityToken, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.token.symbol} {self.alert_type} ${self.target_price}"


