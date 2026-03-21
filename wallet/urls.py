
from django.urls import path
from . import views


urlpatterns = [
    # Add your wallet URLs here
    path('grand-balance/', views.GrandBalanceView.as_view(), name='grand-balance'),
    path('btc-volatility/', views.BTCVolatilityWalletView.as_view(), name='btc-volatility'),
]