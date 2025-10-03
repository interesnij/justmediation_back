from django.core.management import call_command
from config.celery import app


@app.task()
def update_django_cities_light_db():
    """ Обновите базу данных django_cities_light. """
    call_command('cities_light', '--progress')
