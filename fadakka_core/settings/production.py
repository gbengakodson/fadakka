# fadakka_core/settings/production.py
import os
import dj_database_url
from .base import *

DEBUG = False

ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

CORS_ALLOWED_ORIGINS = [
    "https://fadakka-web.onrender.com",
    "https://fadakka.onrender.com",  # Your frontend URL
]

CORS_ALLOW_CREDENTIALS = True

# For testing, temporarily allow all
CORS_ALLOW_ALL_ORIGINS = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f'Fadakka <{os.environ.get("EMAIL_HOST_USER")}>'

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379')