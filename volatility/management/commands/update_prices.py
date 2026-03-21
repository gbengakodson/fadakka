# volatility/management/commands/update_prices.py
import requests
from decimal import Decimal
from django.core.management.base import BaseCommand
from volatility.models import VolatilityToken, UserVolatilityToken
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update token prices from CoinGecko'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Fetching latest prices from CoinGecko...")

        url = "https://api.coingecko.com/api/v3/simple/price"

        # Complete list of supported coins
        coins_list = [
            'bitcoin', 'ethereum', 'cardano', 'shiba-inu',
            'chainlink', 'sui', 'pepe', 'ripple', 'solana',
            'avalanche-2', 'polkadot', 'matic-network', 'dogecoin',
            'uniswap', 'aave', 'litecoin', 'near', 'aptos',
            'arbitrum', 'optimism', 'injective-protocol', 'render-token',
            'the-graph', 'filecoin', 'stacks', 'immutable-x',
            'theta-token', 'fetch-ai', 'gala', 'the-sandbox',
            'binancecoin', 'tron', 'stellar', 'toncoin', 'algorand'
        ]

        # Map token symbols to CoinGecko IDs
        token_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'ADA': 'cardano',
            'SHIB': 'shiba-inu', 'LINK': 'chainlink', 'SUI': 'sui',
            'PEPE': 'pepe', 'XRP': 'ripple', 'SOL': 'solana',
            'AVAX': 'avalanche-2', 'DOT': 'polkadot', 'MATIC': 'matic-network',
            'DOGE': 'dogecoin', 'UNI': 'uniswap', 'AAVE': 'aave',
            'LTC': 'litecoin', 'NEAR': 'near', 'APT': 'aptos',
            'ARB': 'arbitrum', 'OP': 'optimism', 'INJ': 'injective-protocol',
            'RNDR': 'render-token', 'GRT': 'the-graph', 'FIL': 'filecoin',
            'STX': 'stacks', 'IMX': 'immutable-x', 'THETA': 'theta-token',
            'FET': 'fetch-ai', 'GALA': 'gala', 'SAND': 'the-sandbox',
            'BNB': 'binancecoin', 'TRX': 'tron', 'XLM': 'stellar',
            'TON': 'toncoin', 'ALGO': 'algorand'
        }

        params = {
            'ids': ','.join(coins_list),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true'
        }

        try:
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                updated_count = 0

                for token in VolatilityToken.objects.all():
                    coin_id = token_map.get(token.symbol, token.coin_id)
                    coin_data = data.get(coin_id)

                    if coin_data:
                        old_price = token.current_price
                        new_price = Decimal(str(coin_data.get('usd', 0)))

                        if new_price != old_price:
                            token.current_price = new_price
                            if hasattr(token, 'price_change_24h'):
                                token.price_change_24h = Decimal(str(coin_data.get('usd_24h_change', 0)))
                            token.save()
                            updated_count += 1
                            self.stdout.write(f"  {token.symbol}: ${old_price:.2f} → ${new_price:.2f}")

                self.stdout.write(self.style.SUCCESS(f"✅ Updated {updated_count} tokens"))

            else:
                self.stdout.write(self.style.ERROR(f"❌ Failed to fetch prices: {response.status_code}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))