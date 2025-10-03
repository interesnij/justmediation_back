from django.apps import AppConfig


class PromotionAppDefaultConfig(AppConfig):
    """Default configuration for Promotion app."""

    name = 'apps.promotion'
    verbose_name = 'Promotion'

    def ready(self):
        """Enable signals."""
        from . import signals  # noqa
