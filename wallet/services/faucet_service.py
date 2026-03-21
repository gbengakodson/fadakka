import requests
import logging

logger = logging.getLogger(__name__)


class SolanaFaucetService:
    """Service to request test SOL from various faucets"""

    FAUCETS = [
        {
            'name': 'Solana Devnet Faucet',
            'url': 'https://faucet.solana.com/api/request',
            'method': 'POST',
            'data_key': 'address'
        },
        {
            'name': 'SolFaucet',
            'url': 'https://solfaucet.com/api/request',
            'method': 'POST',
            'data_key': 'address'
        }
    ]

    @staticmethod
    def request_test_sol(address, amount=1):
        """Request test SOL from faucets"""
        results = []

        for faucet in SolanaFaucetService.FAUCETS:
            try:
                payload = {faucet['data_key']: address}
                if amount:
                    payload['amount'] = amount

                response = requests.post(
                    faucet['url'],
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    results.append({
                        'faucet': faucet['name'],
                        'success': True,
                        'message': 'Request sent successfully'
                    })
                else:
                    results.append({
                        'faucet': faucet['name'],
                        'success': False,
                        'message': f'Error: {response.status_code}'
                    })

            except Exception as e:
                results.append({
                    'faucet': faucet['name'],
                    'success': False,
                    'message': str(e)
                })

        return results