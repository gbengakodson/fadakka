# wallet/admin_kyc.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import KYCVerification
from .services.notification_service import EmailNotificationService


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'full_name',
        'status_colored',
        'submitted_at',
        'verified_at',
        'view_documents'
    ]
    list_filter = ['status', 'nationality', 'id_type']
    search_fields = ['user__username', 'full_name', 'id_number']
    readonly_fields = ['submitted_at', 'verified_at', 'verified_by']
    actions = ['approve_kyc', 'reject_kyc']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'date_of_birth', 'nationality')
        }),
        ('ID Information', {
            'fields': ('id_type', 'id_number')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason', 'verified_at', 'verified_by')
        }),
        ('Documents', {
            'fields': ('id_front', 'id_back', 'selfie', 'proof_of_address'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )

    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'verified': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )

    status_colored.short_description = 'Status'

    def view_documents(self, obj):
        return format_html(
            '<a href="{}" target="_blank">ID Front</a> | '
            '<a href="{}" target="_blank">Selfie</a>',
            obj.id_front.url if obj.id_front else '#',
            obj.selfie.url if obj.selfie else '#'
        )

    view_documents.short_description = 'Documents'

    def approve_kyc(self, request, queryset):
        from django.utils import timezone
        for kyc in queryset:
            kyc.status = 'verified'
            kyc.verified_at = timezone.now()
            kyc.verified_by = request.user
            kyc.save()

            # Send email notification
            EmailNotificationService.send_kyc_verification_email(
                kyc.user,
                'verified'
            )

        self.message_user(
            request,
            f"{queryset.count()} KYC verification(s) approved."
        )

    approve_kyc.short_description = "Approve selected KYC verifications"

    def reject_kyc(self, request, queryset):
        if 'apply' in request.POST:
            reason = request.POST.get('rejection_reason')
            for kyc in queryset:
                kyc.status = 'rejected'
                kyc.rejection_reason = reason
                kyc.save()

                # Send email notification
                EmailNotificationService.send_kyc_verification_email(
                    kyc.user,
                    'rejected'
                )

            self.message_user(
                request,
                f"{queryset.count()} KYC verification(s) rejected."
            )
            return redirect(request.get_full_path())

        return render(
            request,
            'admin/kyc_rejection.html',
            {'kycs': queryset}
        )

    reject_kyc.short_description = "Reject selected KYC verifications"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'kyc-pending/',
                self.admin_site.admin_view(self.pending_kyc_view),
                name='kyc-pending'
            ),
        ]
        return custom_urls + urls

    def pending_kyc_view(self, request):
        pending = KYCVerification.objects.filter(status='pending')
        return render(
            request,
            'admin/kyc_pending.html',
            {'pending_kycs': pending}
        )
