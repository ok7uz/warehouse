from celery.schedules import crontab
from config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'warehouse',
        'USER': 'postgres',
        "PASSWORD": "pass",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Use Redis as the broker
CELERY_RESULT_BACKEND = 'django-db'  # Store results in Django database
CELERY_CACHE_BACKEND = 'django-cache'  # Use Django cache
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TIMEZONE = 'UTC'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CELERY_BEAT_SCHEDULE = {
    'update-wildberries-sales': {
        'task': 'apps.products.tasks.update_wildberries_sales',
        'schedule': crontab(minute=30),
    },
    'update-ozon-sales': {
        'task': 'apps.products.tasks.update_ozon_sales',
        'schedule': crontab(minute=30),
    },
}