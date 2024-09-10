from celery.schedules import crontab
from config.settings.base import *

from decouple import config

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default=5432, cast=int),
        'OPTIONS': {
            'options': '-c search_path=django,public -c statement_timeout=50000',
        },
        'CONN_MAX_AGE': 6000,
    }
}
