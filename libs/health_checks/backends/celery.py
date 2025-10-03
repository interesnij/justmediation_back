from health_check.contrib.celery.backends import \
    CeleryHealthCheck as BaseCeleryHealthCheck
from .base import AbstractHealthCheckBackend


class CeleryHealthCheck(BaseCeleryHealthCheck, AbstractHealthCheckBackend):
    """Checks that celery is working"""
    _identifier = 'celery'
    _description = 'Celery Health Check'
    QUEUE = None

    @property
    def description(self):
        return f'{self._description} `{self.QUEUE}`'

    def identifier(self):
        return f'{self._identifier}_{self.QUEUE}'
