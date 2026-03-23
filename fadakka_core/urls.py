from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
# Add this test view
def test_view(request):
    return HttpResponse("It works!")

def home(request):
    return HttpResponse("""
        <h1 style="color: #2563eb;">🚀 Fadakka Index API</h1>
        <p>Welcome to Fadakka Index API. Available endpoints:</p>
        <ul>
            <li><a href="/admin/">📊 Admin Panel</a></li>
            <li><a href="/api/coins/">💰 Coins List</a></li>
            <li><a href="/api/wallet/grand-balance/">💳 Grand Balance</a></li>
            <li><a href="/api/wallet/btc-volatility/">📈 BTC Volatility Wallet</a></li>
            <li><a href="/api/volatility/wallet/">⚡ Volatility Wallet</a></li>
            <li><a href="/api/volatility/purchase/">🛒 Purchase V-Index</a></li>
            <li><a href="/api/referral/network/">👥 Referral Network</a></li>
            <li><a href="/api/referral/earnings/">💰 Referral Earnings</a></li>
            <li><a href="/api/referral/downlines/">📋 My Downlines</a></li>
            <li><a href="/api/referral/stats/">📊 Referral Stats</a></li>
            <li><a href="/api/referral/tree/">🌳 Referral Tree</a></li>
            <li><a href="/api/auth/profile/">👤 User Profile</a></li>
        </ul>
        <p style="margin-top: 20px; color: #666;">Server is running properly! ✅</p>
    """)


urlpatterns = [
    # Admin
    path('direct-test/', direct_test),
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('test/', test_view, name='test'),

    # Authentication
    path('api/auth/', include('accounts.urls')),

    # Wallet endpoints
    #path('api/wallet/', include('wallet.urls')),
    #path('api/wallet/', include('wallet.urls_usdc')),  # USDC transactions
    #path('api/wallet/', include('wallet.urls_kyc')),


    # Volatility endpoints
    #path('api/volatility/', include('volatility.urls')),
    #path('api/volatility/', include('volatility.urls_yield')),
    #path('api/volatility/', include('volatility.urls_yield_withdraw')),

    # Referral endpoints - all referral URLs are now included
    #path('api/referral/', include('referral.urls')),
]