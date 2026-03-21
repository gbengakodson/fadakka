from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_coins, name='test-coins'),
    path('', views.CoinListView.as_view(), name='coin-list'),
    path('<int:pk>/', views.CoinDetailView.as_view(), name='coin-detail'),

]