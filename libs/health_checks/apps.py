from django.apps import AppConfig
from celery import current_app
from health_check.plugins import plugin_dir


HEALTH_CHECKS = []


class HealthChecksConfig(AppConfig):
    name = 'libs.health_checks'

    def ready(self):
        """ Зарегистрируйте все пользовательские проверки в плагинах проверки 
        работоспособности """
        from .api import schema  # noqa
        self.enable_checks()

    def enable_checks(self):
        """ Включите все проверки работоспособности, определенные в модуле backends. """
        from . import backends
        plugin_dir.reset()
        backends_to_register = (
            backends.CacheBackend,
            backends.EmailHealthCheck,
            backends.DatabaseBackend,
            backends.FireStoreHealthCheck,
            backends.StripeHealthCheck,
            backends.RedisHealthCheck,
            backends.RabbitMQHealthCheck,
        )
        for backend in backends_to_register:
            HEALTH_CHECKS.append(backend().identifier())
            plugin_dir.register(backend)

        # Сельдерей необходимо зарегистрировать для всех доступных очередей
        for queue in current_app.amqp.queues:
            celery_class_name = 'CeleryHealthCheck' + queue.title()
            celery_class = type(
                celery_class_name,
                (backends.CeleryHealthCheck,),
                {'queue': queue}
            )
            celery_class.QUEUE = queue.title().lower()
            HEALTH_CHECKS.append(celery_class().identifier())
            plugin_dir.register(celery_class)
