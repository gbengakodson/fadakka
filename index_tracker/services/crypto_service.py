# index_tracker/services/crypto_service.py
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
from decimal import Decimal


class CryptoService:
    """Service to fetch and process cryptocurrency data"""

    def __init__(self):
        self.api_key = settings.CRYPTO_API_KEY
        self.base_url = settings.CRYPTO_API_BASE_URL
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

    def get_latest_prices(self, symbols):
        """
        Fetch latest prices for given symbols
        symbols: list of coin symbols ['BTC', 'ETH', 'XRP', ...]
        """
        try:
            response = requests.get(
                f"{self.base_url}/cryptocurrency/quotes/latest",
                headers=self.headers,
                params={'symbol': ','.join(symbols)}
            )

            if response.status_code == 200:
                data = response.json()
                return self._process_price_data(data)
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error fetching prices: {e}")
            return None

    def _process_price_data(self, data):
        """Process and format price data"""
        processed = {}

        for symbol, coin_data in data['data'].items():
            quote = coin_data['quote']['USD']
            processed[symbol] = {
                'name': coin_data['name'],
                'symbol': symbol,
                'price': Decimal(str(quote['price'])),
                'volume_24h': Decimal(str(quote['volume_24h'])),
                'market_cap': Decimal(str(quote['market_cap'])),
                'percent_change_24h': Decimal(str(quote['percent_change_24h'])),
                'last_updated': quote['last_updated']
            }

        return processed

    def get_historical_data(self, symbol, days=99):
        """
        Fetch historical price data for EMA calculation
        Uses CoinMarketCap's historical data endpoint
        """
        try:
            response = requests.get(
                f"{self.base_url}/cryptocurrency/quotes/historical",
                headers=self.headers,
                params={
                    'symbol': symbol,
                    'time_start': (datetime.now() - timedelta(days=days)).isoformat(),
                    'time_end': datetime.now().isoformat(),
                    'interval': 'daily'
                }
            )

            if response.status_code == 200:
                data = response.json()
                return self._calculate_ema(data, days)
            else:
                print(f"Historical API Error: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def _calculate_ema(self, historical_data, period=99):
        """
        Calculate 99-week EMA from historical price data
        Using pandas for accurate EMA calculation
        """
        try:
            # Extract price data
            prices = []
            dates = []

            for quote in historical_data['data']['quotes']:
                prices.append(float(quote['quote']['USD']['close']))
                dates.append(quote['timestamp'])

            # Create pandas Series
            price_series = pd.Series(prices)

            # Calculate EMA
            ema = price_series.ewm(span=period, adjust=False).mean()

            # Get the latest EMA value
            latest_ema = ema.iloc[-1] if not ema.empty else None

            return {
                'current_price': prices[-1] if prices else None,
                'ema_99': float(latest_ema) if latest_ema else None,
                'historical_prices': prices,
                'dates': dates,
                'ema_history': ema.tolist() if not ema.empty else []
            }

        except Exception as e:
            print(f"Error calculating EMA: {e}")
            return None

    def calculate_buy_at_price(self, ema_price):
        """Buy@ = Fadakka Index Price / 2"""
        if ema_price:
            return ema_price / 2
        return None