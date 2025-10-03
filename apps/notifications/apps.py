from django.apps import AppConfig


class NotificationsAppDefaultConfig(AppConfig):
    """Default configuration for Notifications app."""

    name = 'apps.notifications'
    verbose_name = 'Notifications'

    def ready(self):
        """Enable signals and schema definitions.."""
        from . import signals  # noqa
        from .api import schema  # noqa
