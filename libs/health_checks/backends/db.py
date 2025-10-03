from health_check.db.backends import DatabaseBackend as BaseDatabaseBackend
from .base import AbstractHealthCheckBackend


class DatabaseBackend(BaseDatabaseBackend, AbstractHealthCheckBackend):
    """Checks that database is working alright."""
    _identifier = 'database'
    _description = 'Database Health Check'
