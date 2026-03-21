from django.urls import path
from . import views_yield

urlpatterns = [
    path('yield/stats/', views_yield.YieldStatsView.as_view(), name='yield-stats'),
    path('yield/hourly/', views_yield.HourlyYieldView.as_view(), name='yield-hourly'),
    path('yield/daily/', views_yield.DailyYieldView.as_view(), name='yield-daily'),
]