# wallet/admin.py
from django.contrib import admin
from django.contrib import messages
from decimal import Decimal
from .models import GrandBalance, BTCVolatilityWallet, YieldCredit


@admin.register(GrandBalance)
class GrandBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance_usdc', 'total_deposited', 'total_withdrawn']  # Removed last_updated
    search_fields = ['user__username']
    actions = ['credit_test_funds_simple', 'reset_balance']

    def credit_test_funds_simple(self, request, queryset):
        """Simple credit - adds $1000 without extra form"""
        amount = Decimal('1000')
        for balance in queryset:
            balance.balance_usdc += amount
            balance.total_deposited += amount
            balance.save()

        self.message_user(
            request,
            f"✅ Successfully credited ${amount} to {queryset.count()} user(s).",
            messages.SUCCESS
        )

    credit_test_funds_simple.short_description = "💰 Credit $1000 test funds"

    def reset_balance(self, request, queryset):
        """Reset balance to zero for selected users"""
        for balance in queryset:
            balance.balance_usdc = 0
            balance.save()
        self.message_user(
            request,
            f"🔄 Reset {queryset.count()} user(s) balance to $0.",
            messages.SUCCESS
        )

    reset_balance.short_description = "🔄 Reset balance to zero"


@admin.register(BTCVolatilityWallet)
class BTCVolatilityWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'vindex_amount', 'vindex_current_value', 'vol_yield', 'today_yield_count']
    list_filter = ['yield_reset_date']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(YieldCredit)
class YieldCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'day_of_year', 'credit_number', 'credited_at']
    list_filter = ['credited_at', 'day_of_year']
    search_fields = ['user__username', 'transaction_hash']
    date_hierarchy = 'credited_at'