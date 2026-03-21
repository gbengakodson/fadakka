# referral/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main referral views
    path('network/', views.ReferralNetworkView.as_view(), name='referral-network'),
    path('earnings/', views.ReferralEarningsDetailView.as_view(), name='referral-earnings'),
    path('downlines/', views.ReferralDownlineView.as_view(), name='referral-downlines'),
    path('stats/', views.ReferralStatsView.as_view(), name='referral-stats'),
    path('tree/', views.ReferralTreeView.as_view(), name='referral-tree'),

    # Referral link redirect (public endpoint)
    path('r/<str:referral_code>/', views.ReferralRedirectView.as_view(), name='referral-redirect'),

    # Keep mock endpoint for testing if needed
    path('mock/', views.ReferralNetworkOriginalView.as_view(), name='referral-mock'),
]