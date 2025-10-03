from django.apps import AppConfig


class BusinessAppDefaultConfig(AppConfig):
    """Default configuration for Business app."""

    name = 'apps.business'
    verbose_name = 'Business'

    def ready(self):
        """Enable signals and schema definitions."""
        from . import activities_rules  # noqa
        from . import signals  # noqa
        from .api import schema  # noqa
