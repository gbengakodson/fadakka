from django.urls import path
from . import views_yield_withdraw

urlpatterns = [
    path('yield/balance/', views_yield_withdraw.YieldBalanceView.as_view(), name='yield-balance'),
    path('yield/withdraw/', views_yield_withdraw.WithdrawYieldView.as_view(), name='yield-withdraw'),
]