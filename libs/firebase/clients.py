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
  "private_key_id": "1aa3387d9097539225d73f0fd186b0173e9b3d47",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDXoNoF+pRLDM4R\nKbWO9bq0L0MIL8HCpi4DhBSzxj9PMjz3dhJwSDSLF6k95pfnu7xpjSudmpFVMGeX\nCHAaFoh5iYndLUs+Uc69ivGlwHsw0aQQrm+NjUI/xmlD254mNLsDch4L9F2q/n5W\nIuE1uBs4ujsQbxUP8AbJpnAgNhzTCVdcTfcH/ASnBgY7ytDBeROKpLJilojzDyVa\n2LozDW2hlNXMWaZ1aGrZla5oXbfDF73vltSwk/SUZfqQqcbg2nerphDYmypeSl2e\nY4r3f6L3OZFqEE++gbZjKRTFnCOiKibcqCP4JphKMAFQZ2xG01zkMtBuEG9s1dIy\nKRaelGthAgMBAAECggEAUiwTSfn/L0aW9QVvEibk2qu0INeKQHJx0JcyCHyBPd4I\nS8msJyvtEiCXN2a79uydVaAdwfbYcZ17rJvjlJ2HrsFST35mUT59yc+8XQ0oJSeP\nHWhMTKZLW+Bx1xFHiInJxvtjJe0fEP3hCVRLfNxHS2v0/ENIxIUVIR2TV0Mn4ufW\nBMxkg0mOLwsCjbBc9TJ/IqQ4JLb4p8rZhEFnQAp+97tFkgDPhofVDz99cdLA13dd\nqq2Wh8v2pWFJr0IB4SrHl4kKAmBgCE6A2/OCvGUAoIQc4+Wc3o59QIkdkwuM/6Sn\nToQqczevdGM58O43IgNTecoIrpC1rhA749TTvSacLQKBgQD5fBhMH9zE9KUETlji\ninXYiT3+e41rjUumHxxkvoGNVtrxIonWi0LgrOgVlkb1AS42hwzuRvauXMNPDtgO\nGCq8H1VCou3lfjYpPVM9srrb400Lob1ei2QwTvHPZxwRnHlsCB4dYnCPGQYEI26A\nY3LywBy7kCBKJwzMvutl/Ae7WwKBgQDdQmm+9aGWDywmsCD/iDXfoiG4hAmaYZjN\nMhdMsm4EXtWttXufFtWFLoxbyZbkcAK2YoJIL41Hg/1/K09t8e/cUz78KEP8ClCR\nDqh68djJMb6biI/xnkHsoeleMY/YV5KqlPO3Zc9t2+fcecve9dUmUvnWVZMxncD3\nDuI4nXD88wKBgHY2O5kOW+Ai/3Gr4eftrWsdlHdZeaflelvLT/vYXLBo4DLzp5Y1\nxEmLBCj+XL7IgWoq0ZCxpT73C0ARi4QaJV2gBxkc9FYSWH1v5lpMrsdzy1TgnUcI\nCz/smB0rARzDJLFwozxPIYBcXgJl+3zwIk4tgy/IWdRo7mKxb/6RzeQTAoGBAMib\nmn0FAEip4QIC1yhYO2BUA/bj4EEVFBGXxQBJFu7nfR1OWpNXhKiIF8Jw+FqOJCdx\nEWaZlqKszX4rqoyouy0sXQMLDvjJ8VpTy/YMqN1iOMuT+c68ClGeS5SXozAn1lbL\nTl2N9ZBJveNsmqfAhE2HFfZ7CEYIHhjiacGjHfp5AoGALctIJMvlaFxzkW3mI1xf\n5IekNOana3lxZqZhqp81oJWoNHB4GVOkEUKhdbSPLjRFDJSURHBGfA1ouHvNhSyC\nPthQdjuk+P1yLgBY0NeRJC1Q5AOzcEAXUdhunJ/AuGT7b5t1ETI4Qkk2PO9ZC8o7\nuxu1ZETugu2X71s5zuhtqcQ=\n-----END PRIVATE KEY-----\n",
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
