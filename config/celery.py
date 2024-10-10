from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from .settings.base import CELERY_BEAT_SCHEDULE

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('config', broker='redis://localhost:6379/0')
app.conf.enable_utc = False



app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
