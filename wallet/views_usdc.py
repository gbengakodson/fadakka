from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from .models import USDCSolanaWallet, GrandBalance
from .services.usdc_service import USDCSolanaService
import json
import base64
from cryptography.fernet import Fernet
import os
from .services.notification_service import EmailNotificationService

# Initialize encryption
encryption_key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher = Fernet(encryption_key)


class USDCSolanaWalletView(APIView):
    """Get or create user's USDC wallet"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            wallet = USDCSolanaWallet.objects.get(user=request.user)
            return Response({
                'public_key': wallet.public_key,
                'created_at': wallet.created_at
            })
        except USDCSolanaWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)

    def post(self, request):
        # Check if wallet already exists
        if USDCSolanaWallet.objects.filter(user=request.user).exists():
            return Response({'error': 'Wallet already exists'}, status=400)

        # Create new Solana wallet
        service = USDCSolanaService()
        wallet_data = service.create_user_wallet()

        # Encrypt private key before storing
        encrypted_key = cipher.encrypt(wallet_data['private_key'].encode())

        # Save to database
        wallet = USDCSolanaWallet.objects.create(
            user=request.user,
            public_key=wallet_data['public_key'],
            encrypted_private_key=encrypted_key.decode()
        )

        return Response({
            'public_key': wallet.public_key,
            'message': 'Wallet created successfully'
        })


class USDCBalanceView(APIView):
    """Get USDC balance for user's wallet"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            wallet = USDCSolanaWallet.objects.get(user=request.user)
            service = USDCSolanaService()
            balance = service.get_balance(wallet.public_key)

            return Response({
                'public_key': wallet.public_key,
                'balance_usdc': balance
            })
        except USDCSolanaWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)


class USDCDepositAddressView(APIView):
    """Get deposit address for user - auto-create wallet if not exists"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Try to get existing wallet
            wallet = USDCSolanaWallet.objects.get(user=request.user)

            return Response({
                'address': wallet.public_key,
                'memo': '',
                'message': 'Send USDC to this address on Solana network'
            })

        except USDCSolanaWallet.DoesNotExist:
            # Auto-create wallet for user
            try:
                from .services.usdc_service import USDCSolanaService
                import os
                from cryptography.fernet import Fernet
                import base64

                print(f"🔵 Creating new wallet for user: {request.user.username}")

                # Create new Solana wallet
                service = USDCSolanaService()
                wallet_data = service.create_user_wallet()

                # Get or create encryption key
                encryption_key = os.environ.get('ENCRYPTION_KEY')
                if not encryption_key:
                    encryption_key = Fernet.generate_key().decode()
                    print("⚠️ WARNING: Using generated encryption key. Set ENCRYPTION_KEY in .env for production!")

                # Ensure key is in bytes
                if isinstance(encryption_key, str):
                    encryption_key = encryption_key.encode()

                cipher = Fernet(encryption_key)

                # Encrypt private key
                encrypted_key = cipher.encrypt(wallet_data['private_key'].encode())

                # Save to database
                wallet = USDCSolanaWallet.objects.create(
                    user=request.user,
                    public_key=wallet_data['public_key'],
                    encrypted_private_key=encrypted_key.decode()
                )

                print(f"✅ Wallet created for {request.user.username}: {wallet.public_key[:8]}...")

                return Response({
                    'address': wallet.public_key,
                    'memo': '',
                    'message': 'New wallet created. Send USDC to this address.'
                })

            except Exception as e:
                print(f"❌ Error creating wallet: {e}")
                import traceback
                traceback.print_exc()
                return Response(
                    {'error': f'Failed to create wallet: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )





class USDCDepositVerifyView(APIView):
    """Verify a deposit transaction"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tx_signature = request.data.get('transaction_signature')
        expected_amount = request.data.get('amount')

        if not tx_signature or not expected_amount:
            return Response({'error': 'Missing parameters'}, status=400)

        try:
            wallet = USDCSolanaWallet.objects.get(user=request.user)
            service = USDCSolanaService()

            # Verify transaction
            result = service.verify_transaction(tx_signature, expected_amount, wallet)

            if result['verified']:
                # Update GrandBalance
                grand_balance, _ = GrandBalance.objects.get_or_create(user=request.user)
                grand_balance.balance_usdc += float(expected_amount)
                grand_balance.total_deposited += float(expected_amount)
                grand_balance.save()

                # Create transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='deposit',
                    amount=float(expected_amount),
                    solana_tx_hash=tx_signature,
                    solana_from_address=result.get('from', ''),
                    solana_to_address=wallet.public_key,
                    status='completed',
                    completed_at=timezone.now()
                )

                # Send email notification
                try:
                    EmailNotificationService.send_deposit_confirmation(
                        user=request.user,
                        amount=expected_amount,
                        tx_hash=tx_signature,
                        new_balance=float(grand_balance.balance_usdc)
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")  # Log but don't block the response

                return Response({
                    'success': True,
                    'new_balance': float(grand_balance.balance_usdc),
                    'transaction': {
                        'id': transaction.id,
                        'hash': tx_signature,
                        'amount': expected_amount,
                        'status': 'completed'
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Verification failed')
                }, status=400)

        except USDCSolanaWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)


class USDCWithdrawView(APIView):
    """Withdraw USDC to external wallet with KYC check"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_address = request.data.get('to_address')
        amount = request.data.get('amount')

        if not to_address or not amount:
            return Response({'error': 'Missing parameters'}, status=400)

        try:
            amount = float(amount)
            if amount <= 0:
                return Response({'error': 'Invalid amount'}, status=400)

            # Check KYC for large withdrawals
            from .views_kyc import KYCWithdrawCheckView
            check_view = KYCWithdrawCheckView()
            check_result = check_view.post(request).data

            if not check_result['can_withdraw']:
                return Response({
                    'error': 'Withdrawal limit exceeded',
                    'daily_limit': check_result['daily_limit'],
                    'used_today': check_result['used_today'],
                    'remaining': check_result['remaining'],
                    'requires_kyc': check_result.get('requires_kyc', False)
                }, status=400)

            # Check GrandBalance
            grand_balance = GrandBalance.objects.get(user=request.user)
            if grand_balance.balance_usdc < amount:
                return Response({'error': 'Insufficient balance'}, status=400)

            # Get user's wallet
            wallet = USDCSolanaWallet.objects.get(user=request.user)

            # Decrypt private key
            encryption_key = os.environ.get('ENCRYPTION_KEY')
            if encryption_key:
                if isinstance(encryption_key, str):
                    encryption_key = encryption_key.encode()
                cipher = Fernet(encryption_key)
                private_key = cipher.decrypt(wallet.encrypted_private_key.encode()).decode()
            else:
                return Response({'error': 'Encryption key not configured'}, status=500)

            # Create withdrawal
            service = USDCSolanaService()
            result = service.create_withdrawal(private_key, to_address, amount)

            if result['success']:
                # Deduct from GrandBalance
                grand_balance.balance_usdc -= amount
                grand_balance.total_withdrawn += amount
                grand_balance.save()

                # Create transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    solana_tx_hash=result.get('transaction'),
                    solana_to_address=to_address,
                    solana_from_address=wallet.public_key,
                    status='completed',
                    completed_at=timezone.now()
                )

                # Send email notification
                try:
                    EmailNotificationService.send_withdrawal_confirmation(
                        user=request.user,
                        amount=amount,
                        to_address=to_address,
                        new_balance=float(grand_balance.balance_usdc),
                        status='completed'
                    )
                except Exception as e:
                    print(f"Email sending failed: {e}")

                return Response({
                    'success': True,
                    'new_balance': float(grand_balance.balance_usdc),
                    'transaction': {
                        'id': transaction.id,
                        'hash': result.get('transaction'),
                        'amount': amount,
                        'fee': result.get('fee', 0),
                        'net_amount': result.get('net_amount', amount)
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Withdrawal failed')
                }, status=400)

        except USDCSolanaWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)
        except Exception as e:
            logger.error(f"Withdrawal error: {e}")
            return Response({'error': str(e)}, status=500)