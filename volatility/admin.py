from django.contrib import admin
from django.utils import timezone
from .models import VolatilityToken, UserVolatilityToken, VolatilityOrder, YieldDistribution, YieldSchedule, HourlyYield


@admin.register(VolatilityToken)
class VolatilityTokenAdmin(admin.ModelAdmin):
    list_display = ['token_symbol', 'coin_id', 'symbol', 'name', 'current_price', 'monthly_yield_min',
                    'monthly_yield_max', 'created_at']
    list_filter = ['monthly_yield_min', 'monthly_yield_max', 'created_at']
    search_fields = ['coin_id', 'symbol', 'name', 'token_symbol']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['current_price']  # Allow quick price updates
    list_per_page = 25

    fieldsets = (
        ('Token Information', {
            'fields': ('coin_id', 'symbol', 'name', 'token_symbol')
        }),
        ('Pricing', {
            'fields': ('current_price',)
        }),
        ('Yield Settings', {
            'fields': ('monthly_yield_min', 'monthly_yield_max')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserVolatilityToken)
class UserVolatilityTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'balance', 'vol_yield', 'yield_earned_total', 'total_value_display',
                    'last_yield_calculation', 'updated_at']
    list_filter = ['token', 'last_yield_calculation', 'updated_at']
    search_fields = ['user__username', 'token__token_symbol']
    readonly_fields = ['created_at', 'updated_at', 'yield_earned_total']
    list_per_page = 25

    fieldsets = (
        ('User & Token', {
            'fields': ('user', 'token')
        }),
        ('Holdings', {
            'fields': ('balance', 'vol_yield', 'yield_earned_total')
        }),
        ('Timestamps', {
            'fields': ('last_yield_calculation', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_value_display(self, obj):
        try:
            total = (obj.balance * obj.token.current_price) + (obj.vol_yield * obj.token.current_price)
            return f"${total:.2f}"
        except:
            return "N/A"

    total_value_display.short_description = 'Total Value'
    total_value_display.admin_order_field = 'balance'  # Enable sorting


@admin.register(VolatilityOrder)
class VolatilityOrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'token_symbol_display',
        'order_type',
        'amount_display',
        'price_display',
        'total_display',
        'node_fee_display',
        'status_colored',
        'created_at_display'
    ]
    list_filter = ['order_type', 'status', 'created_at']
    search_fields = ['user__username', 'token__token_symbol', 'id']
    readonly_fields = ['created_at', 'completed_at']
    date_hierarchy = 'created_at'
    list_per_page = 50

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'token', 'order_type', 'status')
        }),
        ('Transaction Details', {
            'fields': ('amount', 'price', 'total', 'node_fee')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def token_symbol_display(self, obj):
        return obj.token.token_symbol if obj.token else '-'

    token_symbol_display.short_description = 'Token'
    token_symbol_display.admin_order_field = 'token__token_symbol'

    def amount_display(self, obj):
        return f"{obj.amount:.8f}"

    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'

    def price_display(self, obj):
        return f"${obj.price:.2f}"

    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def total_display(self, obj):
        return f"${obj.total:.2f}"

    total_display.short_description = 'Total'
    total_display.admin_order_field = 'total'

    def node_fee_display(self, obj):
        if hasattr(obj, 'node_fee') and obj.node_fee:
            return f"${obj.node_fee:.2f}"
        return "$0.00"

    node_fee_display.short_description = 'Node Fee'
    node_fee_display.admin_order_field = 'node_fee'

    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return f'<span style="color: {color}; font-weight: bold;">{obj.status.upper()}</span>'

    status_colored.short_description = 'Status'
    status_colored.allow_tags = True
    status_colored.admin_order_field = 'status'

    def created_at_display(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")

    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'

    actions = ['mark_as_completed', 'mark_as_cancelled']

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f"{updated} order(s) marked as completed.")

    mark_as_completed.short_description = "Mark selected orders as completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} order(s) marked as cancelled.")

    mark_as_cancelled.short_description = "Mark selected orders as cancelled"


@admin.register(YieldDistribution)
class YieldDistributionAdmin(admin.ModelAdmin):
    list_display = [
        'user_token',
        'amount_display',
        'percentage',
        'usd_value_display',
        'token_price_display',
        'distributed_at_display'
    ]
    list_filter = ['distributed_at', 'percentage']
    search_fields = ['user_token__user__username', 'user_token__token__token_symbol']
    readonly_fields = ['distributed_at']
    date_hierarchy = 'distributed_at'
    list_per_page = 50

    fieldsets = (
        ('Distribution Details', {
            'fields': ('user_token', 'amount', 'percentage', 'usd_value', 'token_price')
        }),
        ('Timestamp', {
            'fields': ('distributed_at',)
        }),
    )

    def amount_display(self, obj):
        return f"{obj.amount:.8f}"

    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'

    def usd_value_display(self, obj):
        return f"${obj.usd_value:.2f}" if obj.usd_value else "$0.00"

    usd_value_display.short_description = 'USD Value'
    usd_value_display.admin_order_field = 'usd_value'

    def token_price_display(self, obj):
        return f"${obj.token_price:.2f}" if obj.token_price else "$0.00"

    token_price_display.short_description = 'Token Price'
    token_price_display.admin_order_field = 'token_price'

    def distributed_at_display(self, obj):
        return obj.distributed_at.strftime("%Y-%m-%d %H:%M")

    distributed_at_display.short_description = 'Distributed'
    distributed_at_display.admin_order_field = 'distributed_at'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['user_token', 'amount', 'percentage', 'usd_value', 'token_price']
        return self.readonly_fields


# Register additional models if they exist in your models.py
try:
    from .models import YieldSchedule


    @admin.register(YieldSchedule)
    class YieldScheduleAdmin(admin.ModelAdmin):
        list_display = ['user_token', 'day_of_month', 'expected_amount', 'distributed_amount', 'status', 'updated_at']
        list_filter = ['status', 'day_of_month', 'updated_at']
        search_fields = ['user_token__user__username', 'user_token__token__token_symbol']
        readonly_fields = ['created_at', 'updated_at']
        list_per_page = 50

        fieldsets = (
            ('Schedule Details', {
                'fields': ('user_token', 'day_of_month', 'expected_amount', 'distributed_amount', 'status')
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
except (ImportError, NameError):
    pass

try:
    from .models import HourlyYield


    @admin.register(HourlyYield)
    class HourlyYieldAdmin(admin.ModelAdmin):
        list_display = [
            'user_token',
            'hour_of_day',
            'amount_display',
            'usd_value_display',
            'token_price_display',
            'distributed_at_display',
            'transaction_id'
        ]
        list_filter = ['distributed_at', 'hour_of_day']
        search_fields = ['user_token__user__username', 'transaction_id']
        readonly_fields = ['distributed_at']
        date_hierarchy = 'distributed_at'
        list_per_page = 50

        fieldsets = (
            ('Distribution Details', {
                'fields': ('user_token', 'schedule', 'hour_of_day', 'amount', 'usd_value', 'token_price')
            }),
            ('Transaction', {
                'fields': ('transaction_id', 'distributed_at')
            }),
        )

        def amount_display(self, obj):
            return f"{obj.amount:.8f}"

        amount_display.short_description = 'Amount'
        amount_display.admin_order_field = 'amount'

        def usd_value_display(self, obj):
            return f"${obj.usd_value:.2f}" if obj.usd_value else "$0.00"

        usd_value_display.short_description = 'USD Value'
        usd_value_display.admin_order_field = 'usd_value'

        def token_price_display(self, obj):
            return f"${obj.token_price:.2f}" if obj.token_price else "$0.00"

        token_price_display.short_description = 'Token Price'
        token_price_display.admin_order_field = 'token_price'

        def distributed_at_display(self, obj):
            return obj.distributed_at.strftime("%Y-%m-%d %H:%M")

        distributed_at_display.short_description = 'Distributed'
        distributed_at_display.admin_order_field = 'distributed_at'

        def get_readonly_fields(self, request, obj=None):
            if obj:
                return self.readonly_fields + ['user_token', 'schedule', 'hour_of_day', 'amount']
            return self.readonly_fields
except (ImportError, NameError):
    pass

# Admin site customization
admin.site.site_header = 'Fadakka Index Administration'
admin.site.site_title = 'Fadakka Index Admin'
admin.site.index_title = 'Dashboard'