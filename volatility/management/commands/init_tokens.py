from django.core.management.base import BaseCommand
from volatility.models import VolatilityToken


class Command(BaseCommand):
    help = 'Initialize volatility tokens for all 20 coins'

    def handle(self, *args, **options):
        tokens_data = [
            {'coin_id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
            {'coin_id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
            {'coin_id': 'ripple', 'symbol': 'XRP', 'name': 'XRP'},
            {'coin_id': 'binancecoin', 'symbol': 'BNB', 'name': 'BNB'},
            {'coin_id': 'solana', 'symbol': 'SOL', 'name': 'Solana'},
            {'coin_id': 'tron', 'symbol': 'TRX', 'name': 'TRON'},
            {'coin_id': 'dogecoin', 'symbol': 'DOGE', 'name': 'Dogecoin'},
            {'coin_id': 'cardano', 'symbol': 'ADA', 'name': 'Cardano'},
            {'coin_id': 'chainlink', 'symbol': 'LINK', 'name': 'Chainlink'},
            {'coin_id': 'stellar', 'symbol': 'XLM', 'name': 'Stellar'},
            {'coin_id': 'sui', 'symbol': 'SUI', 'name': 'Sui'},
            {'coin_id': 'toncoin', 'symbol': 'TON', 'name': 'Toncoin'},
            {'coin_id': 'shiba-inu', 'symbol': 'SHIB', 'name': 'Shiba Inu'},
            {'coin_id': 'polkadot', 'symbol': 'DOT', 'name': 'Polkadot'},
            {'coin_id': 'aave', 'symbol': 'AAVE', 'name': 'Aave'},
            {'coin_id': 'near', 'symbol': 'NEAR', 'name': 'Near'},
            {'coin_id': 'pepe', 'symbol': 'PEPE', 'name': 'Pepe'},
            {'coin_id': 'render-token', 'symbol': 'RENDER', 'name': 'Render'},
            {'coin_id': 'algorand', 'symbol': 'ALGO', 'name': 'Algorand'},
            {'coin_id': 'filecoin', 'symbol': 'FIL', 'name': 'Filecoin'},
        ]

        for data in tokens_data:
            token, created = VolatilityToken.objects.get_or_create(
                coin_id=data['coin_id'],
                defaults={
                    'symbol': data['symbol'],
                    'name': data['name'],
                    'token_symbol': f"{data['symbol']}-VT",
                    'current_price': 0,  # Will be updated by price feed
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {token.token_symbol}"))
            else:
                self.stdout.write(f"{token.token_symbol} already exists")

        self.stdout.write(self.style.SUCCESS('Volatility tokens initialized!'))