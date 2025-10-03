import uuid
from django.conf import settings
from google.api_core import exceptions
from health_check.exceptions import ServiceUnavailable
from libs.firebase import default_firestore_client
from .base import AbstractHealthCheckBackend


class FireStoreHealthCheck(AbstractHealthCheckBackend):
    """Check that firestore integration works."""
    _identifier = 'firestore'
    _description = 'FireStore Health Check'

    def check_status(self):
        """ Та же проверка, что и при проверке хранилища.
        Мы пытаемся создать, получить, обновить и удалить какой-нибудь тестовый документ.
        """
        if not settings.FIREBASE_ENABLED:
            return
        try:
            health_check_path = f'health_check/{uuid.uuid4()}'
            default_firestore_client.create_or_update(
                path=health_check_path,
                data=dict(test='test')
            )
            default_firestore_client.get(path=health_check_path)
            default_firestore_client.partial_update(
                path=health_check_path,
                data=dict(
                    test='test1'
                )
            )
            default_firestore_client.delete(path=health_check_path)
        except exceptions.GoogleAPIError as error:
            self.add_error(error=ServiceUnavailable(error), cause=error)
