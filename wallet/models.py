# wallet/models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class GrandBalance(models.Model):
    """Main wallet for USDC deposits/withdrawals"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='grand_balance')
    balance_usdc = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_deposited = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ${self.balance_usdc} USDC"

    def can_withdraw(self, amount):
        return self.balance_usdc >= amount


class BTCVolatilityWallet(models.Model):
    """BTC Volatility Index Wallet"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='btc_volatility')

    # BTC V-index (investment amount)
    vindex_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    vindex_purchase_price = models.DecimalField(max_digits=20, decimal_places=2, default=0)  # Price at entry
    vindex_current_value = models.DecimalField(max_digits=20, decimal_places=2,
                                               default=0)  # Current value based on BTC price

    # Vol-yield (accumulated returns)
    vol_yield = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_yield_earned = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # Stats
    last_yield_credit = models.DateTimeField(null=True, blank=True)
    today_yield_count = models.IntegerField(default=0)  # Track 30 daily credits
    yield_reset_date = models.DateField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - V-index: ${self.vindex_amount} | Yield: ${self.vol_yield}"

    @property
    def total_value(self):
        return self.vindex_current_value + self.vol_yield

    def can_sell(self):
        """Can only sell if current value > purchase price"""
        return self.vindex_current_value > self.vindex_purchase_price


class YieldCredit(models.Model):
    """Track each of the 30 daily yield credits"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yield_credits')
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    transaction_hash = models.CharField(max_length=66, unique=True)
    credited_at = models.DateTimeField(auto_now_add=True)
    day_of_year = models.IntegerField()  # 1-365
    credit_number = models.IntegerField()  # 1-30 for that day

    class Meta:
        ordering = ['-credited_at']
        indexes = [
            models.Index(fields=['user', '-credited_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.amount} USDC - #{self.credit_number}"


# wallet/models.py
from django.db import models
from django.contrib.auth.models import User


class USDCSolanaWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usdc_wallet')
    public_key = models.CharField(max_length=44, unique=True)  # Solana public key
    encrypted_private_key = models.TextField()  # Encrypted private key
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.public_key[:8]}..."


class KYCVerification(models.Model):
    """KYC verification records"""
    KYC_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    status = models.CharField(max_length=20, choices=KYC_STATUS, default='pending')

    # Personal information
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=50)
    id_number = models.CharField(max_length=50)
    id_type = models.CharField(max_length=20, choices=[
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('national_id', 'National ID'),
    ])

    # Document uploads
    id_front = models.ImageField(upload_to='kyc/id_front/')
    id_back = models.ImageField(upload_to='kyc/id_back/')
    selfie = models.ImageField(upload_to='kyc/selfie/')
    proof_of_address = models.FileField(upload_to='kyc/address/', null=True, blank=True)

    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='kyc_verified')
    rejection_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"

    @property
    def can_withdraw_large(self):
        """Check if user can withdraw large amounts"""
        return self.status == 'verified'


# Add to wallet/models.py

class Transaction(models.Model):
    """Track all user transactions"""
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('yield', 'Yield'),
        ('referral', 'Referral'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    # Solana transaction details
    solana_tx_hash = models.CharField(max_length=88, unique=True, null=True, blank=True)
    solana_from_address = models.CharField(max_length=44, blank=True)
    solana_to_address = models.CharField(max_length=44, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ${self.amount} - {self.status}"