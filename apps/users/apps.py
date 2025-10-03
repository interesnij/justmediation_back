from django.apps import AppConfig


class UsersAppDefaultConfig(AppConfig):
    """ Конфигурация по умолчанию для пользовательского приложения. """

    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """ Включите сигналы и определения схем. """
        from . import signals  # noqa
        from .api import schema  # noqa
