from django.apps import AppConfig


class AccountingAppDefaultConfig(AppConfig):
    """ Конфигурация по умолчанию для приложения `Бухгалтерия`. """

    name = 'apps.accounting'
    verbose_name = 'Accounting'

    def ready(self):
        """ Включить определения схемы. """
        from .api import schema  # noqa
