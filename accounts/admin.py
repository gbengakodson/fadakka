from django.contrib import admin

# Register your models here.
# accounts/admin.py
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'is_verified', 'referral_code', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'referral_code']
    raw_id_fields = ['user']