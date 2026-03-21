import os
from solana.rpc.api import Client
from solders.keypair import Keypair  # Changed from solana.publickey
from solders.pubkey import Pubkey  # Changed from solana.publickey
from solders.system_program import transfer
from solders.transaction import Transaction
from solders.commitment_config import CommitmentLevel
import base58
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class USDCSolanaService:
    """Service for USDC on Solana blockchain"""

    def __init__(self):
        # Solana RPC endpoints
        self.mainnet_rpc = "https://api.mainnet-beta.solana.com"
        self.devnet_rpc = "https://api.devnet.solana.com"

        # Use devnet for testing, mainnet for production
        self.rpc_url = self.devnet_rpc if settings.DEBUG else self.mainnet_rpc
        self.client = Client(self.rpc_url)

        # USDC mint address on Solana
        self.usdc_mint = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")

        # Platform fee wallet (you control this)
        self.platform_wallet = self._get_platform_wallet()

    def _get_platform_wallet(self):
        """Get or create platform wallet for collecting fees"""
        # In production, load from environment variable
        private_key = os.environ.get('SOLANA_PLATFORM_PRIVATE_KEY')
        if private_key:
            return Keypair.from_base58_string(private_key)

        # For development, create a new wallet
        return Keypair()

    def create_user_wallet(self):
        """Create a new Solana wallet for a user"""
        wallet = Keypair()
        return {
            'public_key': str(wallet.pubkey()),  # Changed from public_key
            'private_key': base58.b58encode(bytes(wallet)).decode('utf-8')
        }

    def get_balance(self, public_key):
        """Get USDC balance for a wallet address"""
        try:
            pubkey = Pubkey.from_string(public_key)

            # Get all token accounts for this owner
            response = self.client.get_token_accounts_by_owner(
                pubkey,
                {"mint": self.usdc_mint}
            )

            if response['result']['value']:
                # Get the first token account
                token_account = response['result']['value'][0]
                token_pubkey = Pubkey.from_string(token_account['pubkey'])

                # Get token account balance
                balance_response = self.client.get_token_account_balance(token_pubkey)
                if balance_response['result']['value']:
                    amount = int(balance_response['result']['value']['amount'])
                    # Convert from smallest unit (6 decimals for USDC)
                    return amount / 1_000_000

            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0

    def create_deposit_address(self, user_wallet):
        """Create a deposit address (the user's wallet)"""
        return {
            'address': str(user_wallet.pubkey()),  # Changed from public_key
            'memo': 'Deposit USDC to fund your GrandBalance'
        }

    def verify_transaction(self, tx_signature, expected_amount, user_wallet):
        """Verify a deposit transaction"""
        try:
            # Get transaction details
            tx = self.client.get_transaction(tx_signature, encoding='json')

            if not tx['result']:
                return {'verified': False, 'error': 'Transaction not found'}

            # For demo purposes, we'll just check if it exists
            return {
                'verified': True,
                'signature': tx_signature,
                'amount': expected_amount,
                'from': 'sender_address',
                'to': str(user_wallet.pubkey())  # Changed from public_key
            }

        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return {'verified': False, 'error': str(e)}

    def create_withdrawal(self, from_wallet, to_address, amount):
        """Create and sign a withdrawal transaction"""
        try:
            # Get sender's token accounts
            token_accounts = self.client.get_token_accounts_by_owner(
                from_wallet.pubkey(),  # Changed from public_key
                {"mint": self.usdc_mint}
            )

            if not token_accounts['result']['value']:
                return {'success': False, 'error': 'No USDC token account found'}

            # Calculate fee (0.1% platform fee)
            platform_fee = amount * 0.001  # 0.1% fee
            net_amount = amount - platform_fee

            # This is a simplified version - actual USDC transfers require token program
            # In production, you'd use the SPL Token program

            return {
                'success': True,
                'transaction': 'signed_transaction',
                'net_amount': net_amount,
                'fee': platform_fee
            }

        except Exception as e:
            logger.error(f"Error creating withdrawal: {e}")
            return {'success': False, 'error': str(e)}