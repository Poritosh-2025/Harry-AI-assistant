"""
Celery configuration for harry project.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'harry.settings')

app = Celery('harry')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'cleanup-expired-otps': {
        'task': 'authentication.tasks.cleanup_expired_otps',
        'schedule': crontab(minute=0),  # Run every hour
    },
}
