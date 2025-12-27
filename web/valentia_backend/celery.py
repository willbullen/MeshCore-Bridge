import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valentia_backend.settings')

app = Celery('valentia_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
