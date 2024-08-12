from .base import *

if config('ENV_NAME') == 'development':
    from .development import *
elif config('ENV_NAME') == 'production':
    from .production import *
else:
    raise ValueError('ENV_NAME must be development or production')
