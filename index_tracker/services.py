# index_tracker/services.py
import requests

import hmac
import hashlib
import time
from decimal import Decimal
from django.conf import settings
from .models import Coin, PriceHistory


class CryptoPriceService:
    """Service to fetch real-time crypto prices"""

    def __init__(self):
        self.api_key = settings.CRYPTO_API_KEY  # Add to settings
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

    def fetch_all_prices(self):
        """Fetch prices for all 20 coins"""
        symbols = [coin[0] for coin in Coin.SYMBOLS]

        try:
            response = requests.get(
                f"{self.base_url}/cryptocurrency/quotes/latest",
                headers=self.headers,
                params={'symbol': ','.join(symbols)}
            )

            if response.status_code == 200:
                data = response.json()
                return self._process_prices(data)
            else:
                print(f"API Error: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching prices: {e}")
            return None

    def _process_prices(self, data):
        """Process API response and update database"""
        updates = []

        for coin_symbol, coin_data in data['data'].items():
            try:
                coin = Coin.objects.get(symbol=coin_symbol)

                quote = coin_data['quote']['USD']
                old_price = coin.current_price_usd

                # Update coin
                coin.current_price_usd = Decimal(str(quote['price']))
                coin.market_cap_usd = Decimal(str(quote['market_cap']))
                coin.volume_24h = Decimal(str(quote['volume_24h']))
                coin.save()

                # Create price history for candlestick
                PriceHistory.objects.create(
                    coin=coin,
                    open_price=old_price or coin.current_price_usd,
                    high_price=max(old_price or 0, coin.current_price_usd),
                    low_price=min(old_price or 0, coin.current_price_usd),
                    close_price=coin.current_price_usd,
                    volume=coin.volume_24h
                )

                updates.append(coin.symbol)

            except Coin.DoesNotExist:
                print(f"Coin {coin_symbol} not found in database")

        return updates