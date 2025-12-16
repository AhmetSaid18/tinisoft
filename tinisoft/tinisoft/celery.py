"""
Celery configuration for Tinisoft project.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tinisoft.settings')

app = Celery('tinisoft')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

