import os
from datetime import timedelta
from pathlib import Path

# Set the base directory path
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security key for the Django application (keep it secret in production)
SECRET_KEY = 'django-insecure-9%470x_op=s5@9yiwf$)b%xj2x9a#!140t=vk6-@d6d4nut%n='

# Debug mode should be False in production
DEBUG = False

# Hosts allowed to access the application
ALLOWED_HOSTS = ["*"]

# Installed applications including Django apps, third-party apps, and custom apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party libraries
    'rest_framework',
    'rest_framework_simplejwt',
    "corsheaders",
    "drf_yasg",
    "django_filters",
    'import_export',

    # Custom applications
    "apps.accounts",
    "apps.companies",
    "apps.marketplaceservice",
    "apps.products",
]

# Middleware configuration for processing requests and responses
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'config.middleware.middleware.JsonErrorResponseMiddleware',
    'config.middleware.middleware.Custom404Middleware',
    'config.middleware.middleware.SimpleJWTAuthenticationMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'config.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],  # Directory for custom templates
        'APP_DIRS': True,  # Enable template loading from installed apps
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

# WSGI application configuration
WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Using SQLite as the database engine
        'NAME': BASE_DIR / 'db.sqlite3',  # Database file location
    }
}

# Password validation settings
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

# Localization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files settings
if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]  # Static files directory in debug mode
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")  # Static files directory in production

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = "/static/"

# Media files settings
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Simple JWT authentication settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=90),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ALLOWED_HOSTS': ['*'],
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME_CLAIM': 'exp',
    'SLIDING_TOKEN_REFRESH_LIFETIME_CLAIM': 'refresh_exp',
}

# Custom user model (commented out, enable if using a custom user model)
AUTH_USER_MODEL = "accounts.CustomUser"

# CORS configuration for cross-origin requests
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = True

# Allowed CORS origins
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]

# REST framework configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    "NON_FIELD_ERRORS_KEY": "errors",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    'DATETIME_FORMAT': "%d.%m.%Y",
}

# CSRF configuration for trusted origins
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173", 'https://*.mydomain.com',
    'https://*.127.0.0.1', 'http://localhost', 'http://localhost:5174', 'http://127.0.0.1:8000',
]
CSRF_COOKIE_SECURE = False

# Maximum size for data upload (100 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 2 ** 20
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

SWAGGER_SETTINGS = {
   'SECURITY_DEFINITIONS': {
      'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
      }
   }
}
