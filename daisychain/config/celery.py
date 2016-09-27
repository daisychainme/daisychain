import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')

from django.conf import settings
from celery import Celery

app = Celery(app='daisychain',
             backend='amqp')

# This reads, e.g., CELERY_ACCEPT_CONTENT = ['json'] from settings.py:
app.config_from_object('django.conf:settings')

# For autodiscover to work, define your tasks in a file called 'tasks.py'.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
