import logging
import uuid
from typing import List, Sequence, Tuple, Union
from unittest import mock
from django.conf import settings
import firebase_admin
from firebase_admin import auth, firestore
from google.cloud.firestore_v1 import (
    Client,
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)
from libs.testing.decorators import assert_not_testing
from apps.users.models import AppUser


__all__ = (
    'FirestoreClient',
    'FirestoreTestClient',
)

logger = logging.getLogger('firestore')


firestore_config = {
  "type": "service_account",
  "project_id": "continual-tine-224909",
  "private_key_id": "0874f173133fd71b3286c8bea4350a391de2c424",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC2kUrlsK/a1B7a\n5S9temiWJS9MQQhDorh5AGTIuOYaHpggRvEcXdLLnpkGo/E2+/lXEF/rfon9PPKK\n59ortriDpGhvgcrtpBhHiEryiGD/VrLQM6/n2JWwlhxTz0ylEqV/vl84r7kYlVuI\nsMmhaWguKkfSi4xNiL208YaPt50AQauatzUtvH7dYwvC6vKe26o6SfQmtqHP/iBw\nlG9SeNP12Cpt7pXxm1KC/vCY/oRyPh052qVl6u5v3FkPOcIXRdSgA7DJjWI7BsyZ\nZuvQMsBPw2j/4jofG6wwDOGv0Z9MoHLx8BoL1hyKbpXsN+isTDS0Q69ceK6gBb/L\nu6W8UhXdAgMBAAECggEABMZaFwSneqNgEb8QjOr0S3+pIutigB1IiejR9bUIAXho\nxYrN+mfZHfQjoOdmB1dZRP5cvf9L3u+R97F3qPt9UGGwXnyeofmcvvL+wgLF1u87\nhFXA7umcpsLFw1vHxPUQ/TkC1c4jictb0hF7vIWvymnWvYLJKJIZq83b2afvBChK\nUCLtKATat/nY3cd0bR7OWk8/px5n2UJfNB/WNhd6cuZVLiS3K12SFNqb7A4jRjPx\nuHhoXWPqBibanUUpDLqOdlEOMiL2znC3xn25KHthy1UX7IaDcrRVYKgHHDk8CZsA\nOicxZVsJVrDD9bfPCGFc1vRI6nbiCAttiaiEgmd2ywKBgQDssLLm0nDC1C7qcBAw\ntsA33yDdMA/+2sDWkV2K+xczJtt5CYiZKvsu7S9+3h5AgvfA8EN96uVfe00zyxd1\nbpJ4DH6dNhuI87Rfh304wEjXZBJ8drSp8yTW0od6khBXmZ+R+Iag9lRnPBjdyZHz\ntpRWrEDoKtyL4rZmIj/xGPO5lwKBgQDFdjxUkWkgg0CAHE6Kt/cVK8UU/zH9bDkF\nxX1Jqipj+C1TdhFYiF0AcruwKS5RrJwd55B3wmRNZLaeybnkYr3eHbsJZB/+4Cso\nf+X6Z0fT+VL4l0qcnECVNCs2TJsmhsN9KDJxcx4k01mesVEx9AVwgarEeSBbCY/a\nvfENz1uSqwKBgBnjOa4FVk/45Si/GQY69sslnHKUzysQwga134VT8TWnCloysL4P\n9WksiAVYRfbIXFC99qPPDUdkNQ11KRuu/FYlB7QqNtjDzvaj2w5Z+Z2VVHBIi3oL\nHfxhCnBdiWwLYWiVxiPUzWZ9LDsV0ODXF2JjdLXv+i9SnKCPHm9AS2gBAoGALVYb\nPfNw5qUb/w4AvnrEgRjelBaPnLbnVLrmLC6ksvU9OudlziTo7XxqOWULHHd8FKWh\nFs4MB3TzNPvt8VD2dPPwiJRzgCpp3k+XNunVpQaelTLvT4vUjC1BKqNmD+9rHOZI\nxqF+r0fTUMs3cDettAohciC5XA2S+M8ZdGlChicCgYEA01CJCuFpGgjjSTkDJdJJ\nA1SSqZykMDBUlwT5f5IkLsbmRdr5d4n3Q5C+Tky0aKuGbjydOEu6/MfgVABTeVer\nlgx5mxXG4cpNLeKbP8Moa5W3GE8lSpq9w688WYs6Hzd3bpsKL04xUTuIQ3FlRFEH\no7Er97A5HlKlVeYRGHXL1iE=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-c9jhq@continual-tine-224909.iam.gserviceaccount.com",
  "client_id": "112247693818316605976",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-c9jhq%40continual-tine-224909.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

class FirestoreClient:
    """ Клиент Google для работы с сервисом Firebase "firestore"
        Учебное пособие с основными принципами работы с Firestone:
        https://firebase.google.com/docs/firestore/data-model
    """

    def __init__(self, *args, **kwargs):
        """Initialize Firestore client.""" 
        credentials = firebase_admin.credentials.Certificate(
            firestore_config
        )
        self.app: firebase_admin.App = firebase_admin.initialize_app(
            credentials,
            name=settings.FIREBASE['CLIENT_NAME']
        )
        self.client: Client = firestore.client(app=self.app)

    def document(self, path: str) -> DocumentReference:
        """ Получить документ ."""
        return self.client.document(path)

    def collection(self, *collection_path: str) -> CollectionReference:
        """ Получите коллекцию. """
        return self.client.collection(*collection_path)

    @assert_not_testing 
    def generate_token(self, user: AppUser):
        """ Сгенерируйте токен пользователя для доступа к Firestore.
        Аргументы:
            user (User): пользователь, который получит доступ к Firestore с 
            сгенерированным JWT знак
        Возвращается:
            (str): сгенерированный токен JWT для пользователя, использующего Firestore
        """
        logger.debug(
            f'Firestore token created.\n'
            f'AppUser: {user.id}'
        )

        return auth.create_custom_token(
            uid=str(user.id),
            app=self.app
        )

    @assert_not_testing
    def create_or_update(self, path: str, data: dict = None):
        """ Способ создания/обновления документа в Firestone.
        Если документ не существует, создается новый. Если документ
        существует, переписывает его с отправленным.

        Аргументы:
            path (str): путь к документу Firestore.
            data (dict): объект для сохранения в качестве документа в Firestore DB
        """
        self.document(path).set(data)

    @assert_not_testing
    def partial_update(self, path: str, data: dict):
        """ Способ обновления полей документа в Firestore.
        Используется для обновления некоторых определенных полей документа.
        Аргументы:
            path (str): путь к документу Firestore.
            data (dict): объектные данные для обновления документа Firestore.
        """
        self.document(path).update(data)

    @assert_not_testing
    def delete(self, path: str):
        """ Способ удаления документа из Firestore.
        Полностью удалите документ из базы данных.
        Аргументы:
            path (str): путь к документу Firestore.
        """
        self.document(path).delete()

    @assert_not_testing
    def get(self, path: str) -> DocumentSnapshot:
        """ Способ получения документа из Firestone.
        Аргументы:
            path (str): путь к документу Firestore.

        Возвращается:
            Document Snapshot: представление документа Firestone.
        """
        return self.document(path).get()

    @assert_not_testing
    def document_exists(self, path: str) -> bool:
        """ Способ проверки наличия документа в Firestone.
        Существующий документ Firestore содержит значение `create_time`.
        Аргументы:
            path (str): путь к документу Firestore.
        Возвращается:
            (bool): существует ли документ или нет
        """
        return self.document(path).get().exists

    @assert_not_testing
    def list(
        self,
        path: str,
        *conditions: List[Tuple[str, str, Union[str, int, list]]]
    ) -> Sequence[DocumentSnapshot]:
        """ Способ получения коллекции из Firestore.
        Аргументы:
            path (str): путь к коллекции Firestone.
            conditions (list): список условий для выполнения запросов. Каждый
                представляет собой "кортеж` со следующим форматом:
                    (поле (str), операция (str), значение)

                Примеры:
                    ('state', '==', 'CA')
                    ('state', 'in', ['CA', 'AC'])
                    ('population', '<', 1000000)

                For more details, see the docs:
                https://firebase.google.com/docs/firestore/query-data/queries

        Возвращается:
            collection (list): список документов Firestone. Каждый из них - это
                `Моментальный снимок документа`.
        """
        # Firestore возвращает коллекцию в качестве генератора документов
        query = self.collection(path)
        for condition in conditions:
            query = query.where(*condition)
        documents = list(query.stream())
        return documents


class FirestoreTestClient(FirestoreClient):
    """ Тестовый клиент следует использовать для тестов, чтобы избежать реальных вызовов API.
    Методы тестирования имитируют запросы к Firestore.
    """

    def __init__(self, *args, **kwargs):
        pass

    def generate_token(self, user: AppUser):
        """ Имитируйте генерацию токена доступа к Firestore.
        Возвращает пользовательский uuid вместо реальных вызовов API.
        """
        return str(uuid.uuid4())

    def _get_fake_object(self):
        """ Верните поддельный объект Firestore.
        Поддельный объект ведет себя как `google.cloud.Объект "Моментальный снимок документа".
        """
        doc = mock.Mock()
        doc.id = mock.PropertyMock(return_value=str(uuid.uuid4()))
        doc.to_dict = mock.Mock(return_value={
            'id': 1,
            'participants': [1, 2],
        })
        return doc

    def create_or_update(self, path: str, data: dict):
        pass

    def partial_update(self, path: str, data: dict):
        pass

    def delete(self, path: str):
        pass

    def get(self, path: str):
        return self._get_fake_object()

    def document_exists(self, path: str):
        return True

    def list(
        self,
        path: str,
        conditions: List[Tuple[str, str, Union[str, int, list]]] = None
    ):
        return list()
