from django.apps import AppConfig


class SocialAppDefaultConfig(AppConfig):
    """Default configuration for Social app."""

    name = 'apps.social'
    verbose_name = 'Social'

    def ready(self):
        """Start up app."""
        from . import signals  # noqa
        from .api import schema  # noqa
