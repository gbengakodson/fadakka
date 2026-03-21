import requests
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PriceService:
    """Service to fetch real-time prices from CoinGecko"""

    COINGECKO_API = "https://api.coingecko.com/api/v3"

    @staticmethod
    def get_all_prices():
        """Fetch prices for all supported coins"""
        try:
            # Complete list of supported coins with their CoinGecko IDs
            coins = [
                'bitcoin',           # BTC
                'ethereum',          # ETH
                'cardano',           # ADA
                'shiba-inu',         # SHIB
                'chainlink',         # LINK
                'sui',               # SUI
                'pepe',              # PEPE
                'ripple',            # XRP
                'solana',            # SOL
                'avalanche-2',       # AVAX
                'polkadot',          # DOT
                'matic-network',     # MATIC
                'dogecoin',          # DOGE
                'uniswap',           # UNI
                'aave',              # AAVE
                'litecoin',          # LTC
                'near',              # NEAR
                'aptos',             # APT
                'arbitrum',          # ARB
                'optimism',          # OP
                'injective-protocol', # INJ
                'render-token',      # RNDR
                'the-graph',         # GRT
                'filecoin',          # FIL
                'stacks',            # STX
                'immutable-x',       # IMX
                'theta-token',       # THETA
                'fetch-ai',          # FET
                'gala',              # GALA
                'sandbox'            # SAND
            ]

            response = requests.get(
                f"{PriceService.COINGECKO_API}/simple/price",
                params={
                    'ids': ','.join(coins),
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_24hr_vol': 'true',
                    'include_market_cap': 'true'
                },
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch prices: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            return None

    @staticmethod
    def get_historical_price(coin_id, days=1):
        """Fetch historical price data"""
        try:
            response = requests.get(
                f"{PriceService.COINGECKO_API}/coins/{coin_id}/market_chart",
                params={
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'hourly'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'prices': data.get('prices', []),
                    'market_caps': data.get('market_caps', []),
                    'total_volumes': data.get('total_volumes', [])
                }
            return None

        except Exception as e:
            logger.error(f"Historical price error: {e}")
            return None

    @staticmethod
    def get_single_price(coin_id):
        """Fetch price for a single coin"""
        try:
            response = requests.get(
                f"{PriceService.COINGECKO_API}/simple/price",
                params={
                    'ids': coin_id,
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'price': Decimal(str(data.get(coin_id, {}).get('usd', 0))),
                    'change_24h': Decimal(str(data.get(coin_id, {}).get('usd_24h_change', 0)))
                }
            return None

        except Exception as e:
            logger.error(f"Single price fetch error: {e}")
            return None