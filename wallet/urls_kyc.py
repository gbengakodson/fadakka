from django.urls import path
from . import views_kyc

urlpatterns = [
    path('kyc/status/', views_kyc.KYCStatusView.as_view(), name='kyc-status'),
    path('kyc/submit/', views_kyc.KYCSubmitView.as_view(), name='kyc-submit'),
    path('kyc/check-withdraw/', views_kyc.KYCWithdrawCheckView.as_view(), name='kyc-check-withdraw'),
]