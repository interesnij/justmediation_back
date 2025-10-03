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
  "private_key_id": "5ab04c2d7cf75a14192fb7342c4e26799cd4cf37",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDQCKAdyWTv0c2X\ngCnk2JZWE5QSnAhmTzf+FxIE+y/3mV029vhpEHv0K+QIVTLVzRIjWh2swpnem+Op\nv3mDIwqFn89baOUZeY1/SDbRPl/j3ujo5leX0jTDs8eI0+zTzo6PWz0GMnmskg59\nd3foXmykaVa+bF8cxczEg7M6pLVHKiVjuOJZ4ZDT5cHDx2F0OY91HlcvmSC1e+oq\nsPGo/9FfUwltG4150JRLOv4GC93JYG+svmqrjpVcJxYO8j6cYlgNK7aWgo5XknPN\nBPFa/qD02dLB7bw9C+cOSp1bWxuNzy1KYL+BvS+cnyr6zR34eyN3JmAZ6FtcyE3W\nSd6HJV2JAgMBAAECggEADz4YjEIrvAIjdhapCyhe8Ijf9DKcT3G9vKdwVa7Za4MA\nUFUNa7ZOXLxECaPDdSSgz/gL/VLnXwcNSexagQQl4tdMJEqV4bVVK6atBI0VTc8R\nAfKRp7E6Vj4DkFgVzcmgSqrw2FXFskIj32fL4HndrDi/JzXtzKAGEj6DmPgFQ8TV\n8U6g3BZs6/wxpVeABFcmEy/JheH7zphjRao2dNzHe8ezZ6aeYiPUUtUga5aE5vbj\nJzln/qkq4hzDQWghipQo2MG/7+Mon2bqjYU0q3+4CpgCDunATvR0ir8GibRWODg4\nXNinRbT4/j0GuVB1UkucIGq1xVtDYpxE1aQAPsBnkQKBgQD8+FdbF5bf3KOXj4qo\nFMstJVB5SmFuMwQIgeOkqMKzdjurCKA8Om6SBFqv7OcKCzLgo+7DTu2Z4JTvP3sK\nLPZt4mmA1XMX66HVv7QVk/J6eavwRceuuGTcbFHYWV3ZZfxjixhITkokd7AUhgty\nrFp86ooX/Qa1/IONuoh4h7SoeQKBgQDShn/7G91p2FZzL91NYHZCQMcC+MohRocp\nny4LDlc1TFe6H+TXS3XKLvfbEKaA76SoxZFMvYW3ol/nqoGR+WPoknWrZp+7fBkj\nJms+peLnfupGvkr/+PP4vgYb9HKrgTYxB6yG4d5B9VFziO6oW7tVlgyATPethrmu\nVxZ1PQc5kQKBgG49i1QXI5jK/j++Ph6hcSlraXZyA6OSd999O0c2hCLRE4+lYq7c\nh/L6Ess34jduSe27gwF6E/FK/ZyFfYkhrwKT+IY8frud5BjSQhhlMPZOr681uZ9a\nnBmy2rf9ufhTiXmX1C0ucQETZ5iKEdMXaRem3ic2DQah1HKfJ3nfKcuBAoGAaikY\n8G+kv3MwZPWGCzbRa6dus7jxdMYz8nEqrriUkXPl6R2cMFUFGOeGZRmIXQx7Y//8\nvU302B0xb4kzvYCdOPJiFAS0F78Ejg0Zl4XfXg1J5lKfT2Ui4hQw0Hf8Oy/1O9Q6\n0+miQnCKmlA6yPs5BHed5jTp0L9XcurHkGct9YECgYEA1f8b/hy1Y5fkNQeE63m4\nPENaGElQJdXWafGhI//jBDr2lWLSah+jEMP6A5UaTXWc+GCYQL/iLczy47yqNWwE\n98QpH5KPxH5uoAxkYwJjQb7MJBd3wotSdFmGpWGyLp24AZ66MfiquA1nxSSkcNfX\nUdXuLsAD93TcuVy9o1rmXHM=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-c9jhq@continual-tine-224909.iam.gserviceaccount.com",
  "client_id": "112247693818316605976",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-c9jhq%40continual-tine-224909.iam.gserviceaccount.com"
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
