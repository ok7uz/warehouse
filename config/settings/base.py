import os
from datetime import timedelta
from pathlib import Path
from decouple import config
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

LOCAL_APPS = [
    
    'apps.company.apps.CompanyConfig',
    'apps.marketplaceservice.apps.MarketplaceserviceConfig',
    'apps.product.apps.ProductConfig',
    'apps.accounts.apps.AccountsConfig',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_celery_results',
    'django_celery_beat'
]

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    *LOCAL_APPS,
    *THIRD_PARTY_APPS,
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 200000

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = False

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ALGORITHM": "HS256",
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Innotrade API',
    'DESCRIPTION': 'Innotrade',
    'VERSION': '1.0.0',
    'OAS_VERSION': '3.1.0',
    'COMPONENT_SPLIT_REQUEST': True,
    'CONTACT': {
        'name': 'Anasxon Azamov',
        'url': 'https://github.com/anasazamov',
        'email': 'anasazamov55@gmail.com',
        'phone_number': '+998990751735',
        'telegram': 't.me/anasxon_azamov',
    },
    'SWAGGER_UI_SETTINGS': {
        'defaultModelRendering': 'model',
    },
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
        'task': 'apps.product.tasks.update_wildberries_sales',
        'schedule': crontab(minute='*/20'),
    },
    'update-wildberries-orders': {
        'task': 'apps.product.tasks.update_wildberries_orders',
        'schedule': crontab(minute='*/20'),
    },
    'update-wildberries-stocks': {
        'task': 'apps.product.tasks.update_wildberries_stocks',
        'schedule': crontab(minute=0, hour=5),
    },
    'update-ozon-sales': {
        'task': 'apps.product.tasks.update_ozon_sales',
        'schedule': crontab(minute='*/20'),
    },
    'update-ozon-orders': {
        'task': 'apps.product.tasks.update_ozon_orders',
        'schedule': crontab(minute='*/20'),
    },
    'update-ozon-stocks': {
        'task': 'apps.product.tasks.update_ozon_stocks',
        'schedule': crontab(minute='*/20'),
    },
    'update_yandex_market_sales': {
        'task': 'apps.product.tasks.update_yandex_market_sales',
        'schedule': crontab(minute='*/20'),
    },
    'update_yandex_market_orders': {
        'task': 'apps.product.tasks.update_yandex_market_orders',
        'schedule': crontab(minute='*/20'),
    },
    'update_yandex_stocks': {
        'task': 'apps.product.tasks.update_yandex_stocks',
        'schedule': crontab(minute='*/20'),
    },
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
