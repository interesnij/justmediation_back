from django.apps import AppConfig


class ForumsAppDefaultConfig(AppConfig):
    """Default configuration for Forums app."""

    name = 'apps.forums'
    verbose_name = 'Forums'

    def ready(self):
        """Enable signals"""
        from . import signals  # noqa
