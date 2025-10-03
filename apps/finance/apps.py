from django.apps import AppConfig


class FinanceAppDefaultConfig(AppConfig):
    """ Конфигурация по умолчанию для финансового приложения ."""

    name = 'apps.finance'
    verbose_name = 'Finance'

    def ready(self):
        """ Включите сигналы и определения схем. """
        from . import webhooks  # noqa
        from .api import schema  # noqa
