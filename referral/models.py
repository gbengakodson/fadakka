from django.db import models
from django.contrib.auth.models import User
from volatility.models import VolatilityOrder  # Import the new order model


class ReferralNode(models.Model):
    """7-tier referral tree"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_node')
    referrer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='downlines')

    # Track all 7 levels as JSON for quick access
    level_1 = models.JSONField(default=list)  # Direct referrals (user ids)
    level_2 = models.JSONField(default=list)
    level_3 = models.JSONField(default=list)
    level_4 = models.JSONField(default=list)
    level_5 = models.JSONField(default=list)
    level_6 = models.JSONField(default=list)
    level_7 = models.JSONField(default=list)

    referral_code = models.CharField(max_length=20, unique=True)
    total_earned = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Referral Node"
        verbose_name_plural = "Referral Nodes"

    def __str__(self):
        return f"{self.user.username} - Code: {self.referral_code}"

    def get_commission_rate(self, level):
        """Get commission percentage for each level"""
        rates = {
            1: 1.00,  # 100% of node fee from direct downline
            2: 0.20,  # 20% of node fee from 2nd generation
            3: 0.10,  # 10% of node fee from 3rd generation
            4: 0.07,  # 7% of node fee from 4th generation
            5: 0.05,  # 5% of node fee from 5th generation
            6: 0.03,  # 3% of node fee from 6th generation
            7: 0.01,  # 1% of node fee from 7th generation
        }
        return rates.get(level, 0)

    def generate_referral_code(self):
        """Generate a unique referral code"""
        import random
        import string

        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not ReferralNode.objects.filter(referral_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)


class NodeFeeDistribution(models.Model):
    """Track commission distributions from volatility token purchases"""
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fees_paid',
        help_text="The user who made the purchase"
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fees_received',
        help_text="The referrer receiving commission"
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2, help_text="Commission amount in USDC")
    level = models.IntegerField(help_text="Referral level (1-7)")

    # Link to the volatility order that generated this fee
    purchase = models.ForeignKey(
        'volatility.VolatilityOrder',
        on_delete=models.CASCADE,
        help_text="The volatility token purchase that generated this commission"
    )

    # Fee breakdown
    node_fee_total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Total 10% node fee from the purchase"
    )
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of node fee received (e.g., 100, 20, 10, etc.)"
    )

    distributed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-distributed_at']
        verbose_name = "Node Fee Distribution"
        verbose_name_plural = "Node Fee Distributions"

    def __str__(self):
        return f"Level {self.level}: {self.from_user.username} → {self.to_user.username} (${self.amount})"


class ReferralStats(models.Model):
    """Aggregated referral statistics per user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_stats')

    # Counts
    total_referrals = models.IntegerField(default=0)
    active_referrals = models.IntegerField(default=0, help_text="Referrals who have made at least one purchase")

    # Earnings
    total_earned = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    pending_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # Level breakdown
    level_1_count = models.IntegerField(default=0)
    level_2_count = models.IntegerField(default=0)
    level_3_count = models.IntegerField(default=0)
    level_4_count = models.IntegerField(default=0)
    level_5_count = models.IntegerField(default=0)
    level_6_count = models.IntegerField(default=0)
    level_7_count = models.IntegerField(default=0)

    # Earnings per level
    level_1_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_2_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_3_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_4_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_5_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_6_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    level_7_earnings = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Referral Statistics"
        verbose_name_plural = "Referral Statistics"

    def __str__(self):
        return f"{self.user.username} - Total Earned: ${self.total_earned}"


class ReferralLink(models.Model):
    """Track referral link clicks and signups"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_links')
    referral_code = models.CharField(max_length=20)
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # If this click led to a registration
    converted_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_link'
    )
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-clicked_at']

    def __str__(self):
        return f"{self.referrer.username} - {self.referral_code} - {self.clicked_at.date()}"