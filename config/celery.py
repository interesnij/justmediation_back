import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('jlp_backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Set up periodic tasks
app.conf.beat_schedule = {
    'Update django_cities_light database': {
        'task': 'libs.django_cities_light.tasks.update_django_cities_light_db',
        # Sometimes resources from geonames.org for django-cities-light
        # (countries, cities and etc files) may be absent and return 404 error.
        # But later in day they appear.
        # More info:
        # https://sentry.saritasa.io/saritasa/jlp/issues/4075/
        'schedule': crontab(minute=0, hour=12),
    },
    'Calculate opportunities stats for mediators': {
        'task': 'apps.forums.tasks.calculate_opportunities_for_today',
        'schedule': crontab(minute=0, hour=14),
    },
    'Generate Invoice': {
        'task': 'apps.business.tasks.generate_invoices',
        # execute every 1st day of month
        'schedule': crontab(minute=0, hour=0, day_of_month=1),
    },
    'Clean old envelopes': {
        'task': 'apps.esign.tasks.clean_old_envelopes',
        # execute every day
        'schedule': crontab(minute=0, hour=0),
    },
    'Cancel failed payments': {
        'task': 'apps.finance.tasks.cancel_failed_payments',
        # execute every day
        'schedule': crontab(minute=0, hour=0),
    },
}
