from django.urls import path
from . import views_usdc

urlpatterns = [
    path('usdc/wallet/', views_usdc.USDCSolanaWalletView.as_view(), name='usdc-wallet'),
    path('usdc/balance/', views_usdc.USDCBalanceView.as_view(), name='usdc-balance'),
    path('usdc/deposit/address/', views_usdc.USDCDepositAddressView.as_view(), name='usdc-deposit-address'),
    path('usdc/deposit/verify/', views_usdc.USDCDepositVerifyView.as_view(), name='usdc-deposit-verify'),
    path('usdc/withdraw/', views_usdc.USDCWithdrawView.as_view(), name='usdc-withdraw'),
    path('usdc/deposit-address/', views_usdc.USDCDepositAddressView.as_view(), name='usdc-deposit-address'),
]