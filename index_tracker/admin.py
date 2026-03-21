from django.contrib import admin

# Register your models here.
# index_tracker/admin.py
from django.contrib import admin
from .models import Coin, PriceHistory, IndexAccess


@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'current_price_usd', 'fadakka_index_price', 'buy_at_price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['symbol', 'name']
    readonly_fields = ['created_at', 'updated_at', 'last_price_update']

    fieldsets = (
        ('Basic Information', {
            'fields': ('symbol', 'name', 'is_active')
        }),
        ('Price Data', {
            'fields': ('current_price_usd', 'market_cap_usd', 'volume_24h')
        }),
        ('Fadakka Index', {
            'fields': ('fadakka_index_price', 'buy_at_price', 'ema_history')
        }),
        ('Price Changes', {
            'fields': ('price_change_24h', 'price_change_7d', 'price_change_30d')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_price_update'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['coin', 'timestamp', 'close_price', 'volume']
    list_filter = ['coin', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(IndexAccess)
class IndexAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'coin', 'paid_at', 'payment_tx_hash']
    list_filter = ['paid_at', 'coin']
    search_fields = ['user__username', 'coin__symbol']