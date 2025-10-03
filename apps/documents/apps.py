from django.apps import AppConfig


class DocumentsAppDefaultConfig(AppConfig):
    """Default configuration for Documents app."""

    name = 'apps.documents'
    verbose_name = 'Documents'

    def ready(self):
        """Enable signals and schema definitions."""
        from . import signals  # noqa
        from .api import schema  # noqa
