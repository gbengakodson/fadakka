# index_tracker/tasks.py
from celery import shared_task
from django.core.management import call_command


@shared_task
def update_prices_task():
    """Task to update cryptocurrency prices"""
    call_command('update_prices')
    return "Prices updated successfully"


@shared_task
def calculate_emas_task():
    """Task to recalculate EMAs"""
    from index_tracker.models import Coin
    from index_tracker.services.crypto_service import CryptoService

    service = CryptoService()
    coins = Coin.objects.filter(is_active=True)

    for coin in coins:
        historical = service.get_historical_data(coin.symbol)
        if historical and historical['ema_99']:
            coin.fadakka_index_price = historical['ema_99']
            coin.buy_at_price = service.calculate_buy_at_price(coin.fadakka_index_price)
            coin.save()

    return "EMAs calculated successfully"