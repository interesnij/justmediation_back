from django.apps import AppConfig


class ESignAppDefaultConfig(AppConfig):
    """Default configuration for ESign app (electronic signing)."""

    name = 'apps.esign'
    verbose_name = 'ESign'

    def ready(self):
        """Enable schema definitions."""
        from .api import schema  # noqa
