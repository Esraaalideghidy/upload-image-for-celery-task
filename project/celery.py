from __future__ import annotations
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')

# Load broker/url from Django settings (we set defaults in settings.py)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
