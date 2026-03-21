from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import GrandBalance, BTCVolatilityWallet

@receiver(post_save, sender=User)
def create_user_wallets(sender, instance, created, **kwargs):
    """Create both wallets for every new user"""
    if created:
        GrandBalance.objects.get_or_create(user=instance)
        BTCVolatilityWallet.objects.get_or_create(user=instance)
        print(f"✅ Wallets created for {instance.username}")

@receiver(post_save, sender=User)
def save_user_wallets(sender, instance, **kwargs):
    """Save wallets when user is saved"""
    if hasattr(instance, 'grand_balance'):
        instance.grand_balance.save()
    if hasattr(instance, 'btc_volatility'):
        instance.btc_volatility.save()