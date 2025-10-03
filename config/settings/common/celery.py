# All default settings for CELERY here
# https://docs.celeryproject.org/en/latest/userguide/configuration.html
CELERY_BROKER_URL = 'amqp://guest@rabbitmq/'
CELERY_RESULT_BACKEND = 'redis://redis/'

CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle','json']

# if this option is True - celery task will run like default functions,
# not asynchronous
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = False

CELERY_IMPORTS = (
    'libs.django_cities_light.tasks',
)
