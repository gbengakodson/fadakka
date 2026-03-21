from solders.keypair import Keypair
import base58

# Generate a new wallet
wallet = Keypair()

# Get public key
public_key = str(wallet.pubkey())
print(f"Public Key (address): {public_key}")

# Get private key in base58 format (for .env)
private_key = base58.b58encode(bytes(wallet)).decode('utf-8')
print(f"Private Key (for .env): {private_key}")

# Also show as bytes array (for Solana CLI format)
print(f"\nPrivate Key (bytes): {list(bytes(wallet))}")

# Save to .env
with open('.env', 'a') as f:
    f.write(f'\nSOLANA_PLATFORM_PRIVATE_KEY={private_key}\n')
    f.write(f'SOLANA_PLATFORM_PUBLIC_KEY={public_key}\n')

print(f"\n✅ Platform wallet saved to .env")
print(f"💰 Fund this wallet with SOL and USDC before processing withdrawals!")