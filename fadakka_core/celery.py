# fadakka_core/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fadakka_core.settings')

app = Celery('fadakka_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule periodic tasks
app.conf.beat_schedule = {
    'update-prices-every-2-minutes': {
        'task': 'volatility.tasks.update_token_prices',
        'schedule': crontab(minute='*/2'),  # Every 2 minutes
    },
    'update-holdings-profit-loss-every-2-minutes': {
        'task': 'volatility.tasks.update_all_holdings_profit_loss',
        'schedule': crontab(minute='*/2'),  # Every 2 minutes
    },
    'check-auto-sell-every-minute': {
        'task': 'volatility.tasks.check_auto_sell',
        'schedule': crontab(minute='*'),  # Every minute
    },
    'distribute-yield-daily': {
        'task': 'volatility.tasks.distribute_yield',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'check-price-alerts-every-minute': {
        'task': 'volatility.tasks.check_price_alerts',
        'schedule': crontab(minute='*'),  # Every minute
    },
}