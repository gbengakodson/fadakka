from django.contrib import admin

# Register your models here.
# referral/admin.py
from django.contrib import admin
from .models import ReferralNode, NodeFeeDistribution


@admin.register(ReferralNode)
class ReferralNodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'referrer', 'referral_code', 'total_earned', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'referral_code']
    readonly_fields = ['created_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'referrer', 'referral_code')
        }),
        ('Earnings', {
            'fields': ('total_earned',)
        }),
        ('Downlines', {
            'fields': ('level_1', 'level_2', 'level_3', 'level_4', 'level_5', 'level_6', 'level_7'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(NodeFeeDistribution)
class NodeFeeDistributionAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'amount', 'level', 'distributed_at']
    list_filter = ['level', 'distributed_at']
    search_fields = ['from_user__username', 'to_user__username']
    date_hierarchy = 'distributed_at'