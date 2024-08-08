from config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['*']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'erp_inno',
        'USER': 'postgres',
        "PASSWORD": "05769452",
        "HOST": "localhost",
        "PORT": 5432,
    }
}
