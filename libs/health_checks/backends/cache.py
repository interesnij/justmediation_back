from health_check.cache.backends import CacheBackend as BaseCacheBackend
from .base import AbstractHealthCheckBackend


class CacheBackend(BaseCacheBackend, AbstractHealthCheckBackend):
    """Checks Django's cache"""
    _identifier = 'cache'
    _description = 'Cache Health Check'
