import logging
import uuid
from functools import wraps
from typing import Iterable, List, Tuple
from unittest.mock import MagicMock
from django.conf import settings
import arrow
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError
from quickbooks import QuickBooks
from quickbooks import objects as qb_objects
from quickbooks.batch import batch_create
from quickbooks.exceptions import (
    AuthorizationException,
    ObjectNotFoundException,
    QuickbooksException,
)
from quickbooks.objects.batchrequest import BatchResponse
from libs.testing.decorators import assert_not_testing
from . import exceptions
from .services import create_qb_object


__all__ = (
    'QuickBooksClient',
    'QuickBooksTestClient',
)


logger = logging.getLogger('quickbooks')
QB_CONFIG = settings.QUICKBOOKS


def auth_required(method):
    """ Декоратор для клиента Quickbooks, который отслеживает токены. """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Проверьте, что токены существуют и срок их действия не истек, и обновите, если возможно
        """
        # проверьте, определены ли `access_token`, `refresh_token` и `realm_id`
        client = self.auth_client
        if not all([client.access_token, client.refresh_token, client.realm_id]):  # noqa
            raise exceptions.NotAuthorized

        if self.is_refresh_token_expired:
            raise exceptions.RefreshTokenExpired

        if self.is_access_token_expired:
            self.refresh_tokens()
        try:
            return method(self, *args, **kwargs)

        except (AuthorizationException, AuthClientError) as error:
            error_msg = f'Authorization error: {error}'
            logger.warning(error_msg)
            raise exceptions.AuthError(error_msg)

    return wrapper


class QuickBooksClient:
    """ Клиент, используемый для аутентификации и взаимодействия с Quickbooks API.
    Этот клиент использует 2 различных пакета python для выполнения работы с QB API:
        - intuit lib - общий клиент авторизации для приложений Intuit
        - quickbooks - пакет для взаимодействия с QB API (CRUD-операции и т.д.)
    """

    # уровень доступа, который пользователь QB предоставляет приложению
    scopes = [Scopes.ACCOUNTING]

    def __init__(
        self,
        state_token: str = None,
        access_token: str = None,
        refresh_token: str = None,
        id_token: str = None,
        realm_id: str = None,
        expires_in: int = None,
        x_refresh_token_expires_in: int = None,
        user=None
    ):
        """ В нем клиент Quickbooks.
        Чтобы инициализировать клиент QB, нам нужно создать клиент `auth` и клиент `api`
        инициализация и запоминание информации об истечении срока действия токенов.
        Атрибуты:
            state_token (str) - уникальный идентификатор пользователя в серверной части, 
                соответствующий возвращено после получения ответа о согласии
            access_token (str) - основной токен авторизации пользователя, если он уже
                вошел в систему (срок действия истекает через 60 минут)
            refresh_token (str) - токен обновления пользователя, срок действия которого истек
                токен авторизации может быть обновлен (срок действия истекает через 100 дней)
            id_token (str) - идентификационный токен для потока OpenID
            realm_id (str) - Область QBO/идентификатор компании
            expire_in (int) - временная метка, по истечении срока действия `access_token`
            x_refresh_token_expires_in (int) - временная метка при `refresh_token`
            expires user - некоторый пользователь приложения, от имени которого 
                выполняются запросы QB
        """
        self.auth_client = AuthClient(
            client_id=QB_CONFIG['CLIENT_ID'],
            client_secret=QB_CONFIG['CLIENT_SECRET'],
            redirect_uri=f'{settings.BASE_URL}/{QB_CONFIG["AUTH_REDIRECT_URL"]}',  # noqa
            environment=QB_CONFIG['ENVIRONMENT'],
            state_token=state_token,
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            realm_id=realm_id,
        )
        self.user = user
        self.access_expires_in = expires_in
        self.refresh_expires_in = x_refresh_token_expires_in  # noqa

        self.api_client = None
        # Мы можем использовать в нем quickbooks_api_client, только если у нас есть 
        # токен обновления
        if self.refresh_token and self.realm_id:
            self._init_api_client()

    def _init_api_client(self):
        """ Инициируйте клиент для взаимодействия с api. """
        self.api_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=self.refresh_token,
            company_id=self.realm_id,
        )

    @property
    def realm_id(self):
        return self.auth_client.realm_id

    @property
    def access_token(self):
        return self.auth_client.access_token

    @property
    def refresh_token(self):
        return self.auth_client.refresh_token

    @property
    def id_token(self):
        return self.auth_client.id_token

    @property
    def is_access_token_expired(self) -> bool:
        """ Проверьте, истек ли срок действия токена доступа. """
        return self._is_token_expired(self.access_expires_in)

    @property
    def is_refresh_token_expired(self) -> bool:
        """ Проверьте, истек ли срок действия токена обновления. """
        return self._is_token_expired(self.refresh_expires_in)

    @assert_not_testing
    def get_authorization_url(self, state_token=None) -> str:
        """ Сгенерируйте URL-адрес авторизации, на который будет перенаправлен пользователь.

        Пользователь будет перенаправлен на страницу входа в QuickBooks, где его
        попросят предоставить доступ к приложению. В случае успешного ответа
        пользователь будет перенаправлен на серверную часть `AUTH_REDIRECT_URL` с
        `access_code`. Серверная часть будет отвечать за обмен
        `access_code` для `access_token` и `refresh_token` с использованием метода
        `get_bearer_token`.

        Атрибуты:
            state_token (str) - уникальный идентификатор пользователя в серверной части, 
                соответствующий возвращено после получения ответа о согласии
        """
        return self.auth_client.get_authorization_url(
            scopes=self.scopes, state_token=state_token
        )

    @assert_not_testing
    def get_bearer_token(self, auth_code: str, realm_id=None) -> dict:
        """ Получите access_token и обновите_token, используя код авторизации.
        Этот метод завершает процесс авторизации пользователя и обменивается
        `access_code` для доступа к токенам и обновления информации об их
        истечение.

        Атрибуты:
            auth_code (str) - код доступа, взятый из перенаправления QB auth url
            realm_id (str) - идентификатор компании/домена в QB
        """
        try:
            self.auth_client.get_bearer_token(
                auth_code=auth_code, realm_id=realm_id
            )
        except AuthClientError as e:
            # Просто печатаю здесь status_code, но его можно использовать для повторной попытки
            # рабочий процесс и т.д
            logger.error(f'{e.status_code} {e.intuit_tid} {e.content}')
            raise e
        access_expires_in, refresh_expires_in = self._get_expiration_timestamps()  # noqa
        return {
            'realm_id': self.realm_id,
            'access_token': self.access_token,
            'expires_in': access_expires_in,
            'refresh_token': self.refresh_token,
            'x_refresh_token_expires_in': refresh_expires_in,
            'id_token': self.id_token,
        }

    @assert_not_testing
    def refresh_tokens(self):
        """ Обновите токены доступа и инициализируйте клиент API новыми токенами. """
        self.auth_client.refresh()
        self._init_api_client()
        self.access_expires_in, self.refresh_expires_in = \
            self._get_expiration_timestamps()

    @assert_not_testing
    def get_customers(self, limit: int = None) -> List[qb_objects.Customer]:
        """ Загружайте клиентов из API. """
        return self._get_objects(qb_objects.Customer, limit)

    @assert_not_testing
    def get_customer(self, customer_id: int) -> qb_objects.Customer:
        """ Получите `клиента` по идентификатору из API. """
        return self._get_object(qb_objects.Customer, customer_id)

    @assert_not_testing
    def get_invoice(self, invoice_id: int) -> qb_objects.Invoice:
        """ Получите "счет-фактуру" по идентификатору из API. """
        return self._get_object(qb_objects.Invoice, invoice_id)

    @assert_not_testing
    @auth_required
    def save_object(self, qb_object):
        """ Ярлык для сохранения объекта QB в QuickBooks. """
        try:
            return qb_object.save(qb=self.api_client)
        except QuickbooksException as e:
            # повторяющиеся ошибки имеют свои отдельные коды
            if e.error_code == 6240:
                raise exceptions.DuplicatedObjectError(
                    f"The {qb_object.qbo_object_name} already exists: {e}"
                )
            raise exceptions.SaveObjectError(
                f"Can't save {qb_object.qbo_object_name}: {e}"
            )

    @assert_not_testing
    @auth_required
    def batch_create(self, objects: Iterable) -> BatchResponse:
        """ Сделайте запрос на пакетное создание списка объектов.

        Возвращает пакетный ответ, который имеет:
            batch_responses: список ответов от API
            original_list: список порядковых qb_objects
            successes: список qb_objects, которые были сохранены
            faults: список qb_objects, которые не были сохранены
        """
        return batch_create(objects, qb=self.api_client)

    def _is_token_expired(self, expires_in: int) -> bool:
        """ Ярлык для проверки того, истек ли срок действия токена. """
        if not expires_in:
            return True
        return arrow.utcnow() > arrow.get(expires_in)

    def _get_expiration_timestamps(self) -> Tuple[int, int]:
        """ Ярлык для преобразования "истечения срока действия" в временные метки, начиная с 
        этого момента.

        QuickBooks возвращает срок действия токенов в виде простого количества секунд,
        что означает, как долго токен будет действителен. Для выполнения `is_expired`
        проверьте, что нам нужно сравнить текущее время со временем, когда токен будет
        становятся недействительными, рассчитанные с "сейчас".
        """
        now = arrow.utcnow().timestamp
        access_expires_in = now + self.auth_client.expires_in
        refresh_expires_in = now + self.auth_client.x_refresh_token_expires_in
        return access_expires_in, refresh_expires_in

    @assert_not_testing
    @auth_required
    def _get_objects(self, qb_class, limit: int = 1000) -> List:
        """ Загрузите объекты qb для Quickbooks API.
        Аргументы:
            qb_class: класс объектов QB для загрузки
            limit (int):
                Ограничение на количество объектов, которые должны быть загружены, если 
                ограничение равно None, то мы устанавливаем ограничение на количество элементов 
                в Quickbooks db, другими словами, мы загружаем все.
        """
        count = qb_class.count(qb=self.api_client)
        limit, offset = limit or 1000, 1
        objects = []
        while len(objects) != count:
            results = qb_class.all(
                qb=self.api_client, start_position=offset, max_results=limit
            )
            offset = offset + len(results)
            objects.extend(results)
        return objects

    @assert_not_testing
    @auth_required
    def _get_object(self, qb_class, object_id: int):
        """ Ярлык для получения объекта QB в QuickBooks. """
        try:
            return qb_class.get(id=object_id, qb=self.api_client)
        except ObjectNotFoundException:
            raise exceptions.ObjectNotFound(
                f'{qb_class.qbo_object_name} not found in QuickBooks'
            )


class QuickBooksTestClient(QuickBooksClient):
    """ Отдельный тестовый клиент для QuickBooks, чтобы избежать реальных вызовов API. """

    auth_client_mock = MagicMock(
        realm_id=str(uuid.uuid4()),
        access_token=str(uuid.uuid4()),
        refresh_token=str(uuid.uuid4()),
        id_token=str(uuid.uuid4()),
        state_token=str(uuid.uuid4()),
        #expires_in=arrow.utcnow().timestamp() + 3600,
        #x_refresh_token_expires_in=arrow.utcnow().timestamp() + 3600,
    )

    api_client_mock = MagicMock(
        auth_client=auth_client_mock,
        refresh_token=auth_client_mock.refresh_token,
        company_id=auth_client_mock.realm_id,
    )

    def __init__(self, *args, **kwargs):
        """ Переопределена инициализация клиента для имитирования реальных вызовов API. """
        # специальный метод, который можно использовать в тестах для правильной установки
        # `auth_client`
        self.auth_client = self._get_auth_client(*args, **kwargs)
        self.user = kwargs.get('user')
        self.access_expires_in = self.auth_client.expires_in
        self.refresh_expires_in = self.auth_client.x_refresh_token_expires_in
        self.api_client = None
        # Мы можем использовать в нем quickbooks_api_client, только если у нас есть токен 
        # обновления
        if self.refresh_token and self.realm_id:
            self._init_api_client()

    def _init_api_client(self):
        """ Переопределена инициализация клиента для имитирования реальных вызовов API. """
        self.api_client = self.api_client_mock

    def _get_auth_client(self, *args, **kwargs):
        """ Специальный метод, который можно использовать в тестах для настройки другой 
        аутентификации.
        """
        return self.auth_client_mock

    def get_authorization_url(self, state_token=None) -> str:
        """ Переопределенный метод для имитирования реальных вызовов API. """
        return 'https://fake-url.com'

    def get_bearer_token(self, auth_code: str, realm_id=None) -> dict:
        """ Переопределенный метод для имитирования реальных вызовов API. """
        return {
            'realm_id': self.realm_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'id_token': self.id_token,
        }

    @auth_required
    def get_customers(self, limit: int = None) -> List[qb_objects.Customer]:
        """ Переопределенный метод для имитирования реальных вызовов API. """
        customer = self.get_customer(1)
        return [customer]

    @auth_required
    def get_customer(self, customer_id: int) -> qb_objects.Customer:
        """ Переопределенный метод для имитирования реальных вызовов API ."""
        return self._get_object(qb_objects.Customer, 1)

    @auth_required
    def get_invoice(self, invoice_id: int) -> qb_objects.Invoice:
        """ Переопределенный метод для имитирования реальных вызовов API """
        return self._get_object(qb_objects.Invoice, 1)

    @auth_required
    def save_object(self, qb_object):
        """ Переопределенный метод для имитирования реальных вызовов API """
        return qb_object

    @auth_required
    def _get_object(self, qb_class, object_id: int):
        """ Ярлык для получения объекта QB в QuickBooks. """
        try:
            return self._qb_class_get(qb_class)
        except ObjectNotFoundException:
            raise exceptions.ObjectNotFound(
                f'{qb_class.qbo_object_name} not found in QuickBooks'
            )

    def _qb_class_get(self, qb_class):
        """ Специальный метод может быть использован для другого поведения `qb_class.get`. 
        """
        if qb_class == qb_objects.Invoice:
            return create_qb_object(
                qb_objects.Invoice,
                Id=1,
                SyncToken=0
            )

        if qb_class == qb_objects.Customer:
            return create_qb_object(
                qb_objects.Customer,
                Id=1,
                DisplayName="Amy's Bird Sanctuary",
                GivenName='Amy',
                FamilyName='Lauterbach',
                PrimaryEmailAddr=create_qb_object(
                    qb_objects.EmailAddress,
                    Address='Birds@Intuit.com'
                ),
                CompanyName="Amy's Bird Sanctuary"
            )
