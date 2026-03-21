from django.urls import path
from . import views

urlpatterns = [
    path('tokens/', views.VolatilityTokenListView.as_view(), name='volatility-tokens'),
    path('user-tokens/', views.UserVolatilityTokensView.as_view(), name='user-volatility-tokens'),
    path('buy/', views.BuyVolatilityTokenView.as_view(), name='buy-volatility-token'),
    path('sell/', views.SellVolatilityTokenView.as_view(), name='sell-volatility-token'),
    path('orders/', views.UserOrderHistoryView.as_view(), name='volatility-orders'),
    path('realtime-prices/', views.RealTimePricesView.as_view(), name='realtime-prices'),
    path('price-alerts/', views.PriceAlertView.as_view(), name='price-alerts'),
    path('price-alerts/<int:alert_id>/', views.PriceAlertView.as_view(), name='price-alert-delete'),
    path('portfolio-analytics/', views.PortfolioAnalyticsView.as_view(), name='portfolio-analytics'),
    path('yield-distributions/', views.YieldDistributionsView.as_view(), name='yield-distributions'),
    path('withdraw-yield/', views.WithdrawYieldView.as_view(), name='withdraw-yield'),
    path('yield/stats/', views.YieldStatsView.as_view(), name='yield-stats'),
    path('yield/hourly/', views.YieldHourlyView.as_view(), name='yield-hourly'),
    path('yield/daily/', views.YieldDailyView.as_view(), name='yield-daily'),
    path('yield/balance/', views.YieldBalanceView.as_view(), name='yield-balance'),
]