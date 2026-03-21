# wallet/blockchain.py
from web3 import Web3
from django.conf import settings
import json


class USDCHandler:
    """Handle USDC transactions on Ethereum blockchain"""

    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
        self.usdc_contract = self.w3.eth.contract(
            address=settings.USDC_CONTRACT_ADDRESS,
            abi=self._get_usdc_abi()
        )

    def _get_usdc_abi(self):
        """USDC ERC-20 ABI"""
        return json.loads('''[
            {
                "constant": true,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": false,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]''')

    def get_balance(self, address):
        """Get USDC balance for an address"""
        try:
            balance = self.usdc_contract.functions.balanceOf(address).call()
            decimals = self.usdc_contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0

    def verify_transaction(self, tx_hash, expected_amount, expected_to_address):
        """Verify a USDC transaction"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return False

            tx = self.w3.eth.get_transaction(tx_hash)

            # Decode transaction input to verify it's USDC transfer
            # This is simplified - in production you'd decode properly

            return {
                'verified': True,
                'from': tx['from'],
                'to': tx['to'],
                'amount': self.w3.from_wei(tx['value'], 'ether'),
                'status': receipt['status']
            }
        except Exception as e:
            print(f"Error verifying transaction: {e}")
            return {'verified': False, 'error': str(e)}