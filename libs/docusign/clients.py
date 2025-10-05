import logging
import time
from typing import List
from urllib.parse import quote, urlencode
from django.conf import settings
import docusign_esign as docusign
from docusign_esign import (
    Document,
    EnvelopeDefinition,
    EnvelopesApi,
    EventNotification,
    Recipients,
    ReturnUrlRequest,
    Signer,
)
from docusign_esign.client.api_exception import ApiException
from docusign_esign.client.auth.oauth import Account, OAuthToken, OAuthUserInfo
from . import exceptions
from .constants import DS_CONFIG, ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SENT


__all__ = (
    'DocuSignClient',
)

logger = logging.getLogger('docusign')


class DocuSignImpersonalizedClientMixin:
    """ Смешивание со всем процессом авторизации, олицетворенным DocuSign.
    Для каждого пользователя должен быть отдельный экземпляр клиента.
    Смешивание обеспечивает возможность:
        1. Проверьте, предоставил ли клиент уже "согласие" на выполнение приложением justmediationhub
        действия от имени пользователя (`is_consent_obtained`).
        2. Разрешить установить токен JWT для клиента API, чтобы сделать олицетворенный
        запросы на регистрацию документов.

    Docs:
        https://developers.docusign.com/esign-rest-api/guides/authentication/
        oauth2-jsonwebtoken

    Использование:
        client = DocuSignClient(user_id='...')

        # если у клиента уже есть согласие -> просто получите токен для него
        if client.is_consent_obtained():
            client.set_jwt_token()
        else:
            link = client.get_consent_link()
            # перенаправьте ссылку в браузере и получите `код` из возвращенного ответа
            code = link.redirect().get_code()  # pseudo code
            client.process_consent(code)
            client.set_jwt_token()

        # выполните некоторые действия с DocuSign (отправьте конверт и т.д.)
        ....

        # обновите токен, если это необходимо
        client.update_token()

    """
    # DocuSign user GUID
    user_id = None
    # Учетная запись пользователя DocuSign по умолчанию
    default_account = None
    # флаг, который определяет, был ли токен уже получен
    token_received = False
    # отметка времени в секундах, когда истечет срок действия последнего полученного токена
    token_expires_timestamp = 0

    def __init__(
        self, user_id: str = None, default_account: dict = None,
        *args, **kwargs
    ) -> None:
        """Инициализировать атрибуты класса
        Атрибуты:
            user_id (str) - идентификатор пользователя в DocuSign, если он известен, или нет
            default_account (dict) - данные учетной записи пользователя по умолчанию, если они известны
        """
        self.user_id = user_id or self.user_id
        self.default_account = default_account or self.default_account

    def update_token(self):
        """ Ярлык для обновления токена клиента с истекшим сроком действия, если это необходимо. """
        is_expired = (
            self._get_current_timestamp() > self.token_expires_timestamp
        )
        if self.user_id and (not self.token_received or is_expired):
            self.set_jwt_token()

    def is_consent_obtained(self) -> bool:
        """ Проверьте, получено ли уже согласие обезличенного пользователя.
        Можно определить, что пользователь уже дал свое согласие, попытавшись
        получить и установить свой токен JWT с существующим идентификатором пользователя (GUID) 
        в DocuSign клиент. Если метод получает аргумент `user_id` и завершается успешно с
        авторизация -> согласие пользователя существует и является действительным. 
        В противном случае учтите, что у пользователя нет согласия.

        После использования этого метода в случае отсутствия "согласия" настоятельно рекомендуется
        рекомендуется получить ссылку на получение согласия `get_consent_link`.

        Возвращается:
            (bool) - флажок, если пользователь уже дал свое согласие
        """
        if not self.user_id:
            return False

        try:
            self._get_jwt_token(log_error=False)
            return True
        except (ApiException, exceptions.GetJWTTokenException):
            return False

    def process_consent(self, code: str) -> str:
        """ Способ обработки полученного согласия и сохранения связанных с ним пользовательских 
        данных.

        Перед вызовом этого метода мы должны получить "согласие" пользователя
        выдавать запросы приложения за его собственные по ссылке get from
        метод `get_consent_link`, после перехода по этой ссылке с помощью браузера там
        будет возвращен специальный "код", который следует использовать в этом методе.

        Тогда этот метод будет:
            1. Обменяйте "код" на токен доступа пользователя, чтобы получить `user_id` от
            метод `get_user_info` позже.
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-code-grant#step-2-obtain-the-access-token)

            2. Получите информацию о пользователе и получите "user_id" из возвращенных данных и запомните
            `default_account" из информации о пользователе.
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-jsonwebtoken#step-4-retrieve-user-account-data)

        После использования этого метода настоятельно рекомендуется вызвать
        `set_jw_token` для выполнения олицетворенных запросов от клиента DocuSign.

        Атрибуты:
            code (str) - код, возвращаемый после перехода по ссылке из
            `get_consent_link` в браузере

        Возвращается:
            (str) - олицетворенный идентификатор пользователя в DocuSign
        """
        assert code, '`code` must be set'
        token = self._exchange_code_to_access_token(code)
        user_data = self._get_user_info(token.access_token)
        self.user_id = user_data.sub
        self.default_account = self._get_default_account(user_data)
        return self.user_id

    def set_jwt_token(self, refresh_default_account=False) -> None:
        """ Способ установки токена DocuSign JWT.
        Методы обрабатывают настройку токена JWT для олицетворяемого DocuSign API
        запросы.

        Он получает токен DocuSign JWT, устанавливает его для текущего клиента, получает
        `default_account` из user_data, если это необходимо, и обновляет токен
        информация об истечении срока действия.

        Атрибуты:
            refresh_default_account (bool) - флаг, если пользователь `default_account`
            должен быть обновлен

        """
        assert self.user_id, '`user_id` must be set'
        # получение токена JWT для олицетворенных запросов
        jwt_token = self._get_jwt_token()
        # используйте пользовательскую настройку токена доступа, потому что внезапно DocuSign 
        # API SDK не добавляет ключевое слово аутентификации `Bearer`, поэтому все запросы 
        # завершаются ошибкой (401)
        self._set_access_token(jwt_token)

        # при необходимости запомните учетную запись пользователя по умолчанию
        if refresh_default_account or not self.default_account:
            user_data = self._get_user_info(jwt_token.access_token)
            self.default_account = self._get_default_account(user_data)
            # установите базовый URI учетной записи по умолчанию в качестве пути к 
            # базовому клиентскому api
            self._set_base_uri()

        self._update_token_info()

    def get_consent_link(self, state: str = None) -> str:
        """ Получите ссылку DocuSign, чтобы получить согласие пользователя.
        Когда приложение проходит аутентификацию для выполнения действий от имени
        пользователя (обезличенного), этому пользователю будет предложено дать согласие на
        набор областей (наборов разрешений), которые запросило приложение, если только оно 
        ранее уже не предоставило это согласие.

        Когда эта ссылка будет открыта на стороне интерфейса:
            1. Осуществил перенаправление по этой ссылке на DocuSign и
            получил согласие.
            2. После получения согласия DocuSign перенаправляет на серверную часть
            `обратный вызов` с параметрами `код` и `состояние`.

        Docs:
        https://developers.docusign.com/esign-rest-api/guides/authentication/
        obtaining-consent#individual-consent

        Атрибуты:
            state (str) - уникальный идентификатор пользователя на серверной части, 
            соответствующий возвращаемому после получения ответа о согласии
        Возвращается:
            (str) - ссылка на страницу получения контента DocuSign
        """
        args = {
            'response_type': 'code',
            'scope': 'signature impersonation',
            'client_id': self.integration_key,
            'redirect_uri': self.consent_redirect_url,
            'state': state
        }
        # docusign неправильно работает, когда "пробел` заменяется на `+` в ссылке
        # итак, вот `quote_via=цитата`, где `пробел` заменен на `%20`
        query_str = urlencode(args, quote_via=quote)
        return f'https://{self.oauth_host_name}/oauth/auth?{query_str}'

    def _set_access_token(self, token: OAuthToken) -> None:
        """ Ярлык для переопределения метода SDK по умолчанию `client.set_access_token`.
        Оригинальный метод SDK устанавливает неверно сформированный токен авторизации без 
        "предъявителя" ключевое слово, которое приводит к 401 несанкционированной ошибке в 
        DocuSign rest api запросы.

        Атрибуты:
            токен (OAuth Token) - объект токена JWT, который должен быть установлен в качестве
            авторизации

        """
        self.client.default_headers['Authorization'] = (
            f'Bearer {token.access_token}'
        )

    def _set_base_uri(self) -> None:
        """ Ярлык для установки базового URI учетной записи по умолчанию для клиента.
        Без этого шага все запросы API не будут успешными, поэтому нам нужно
        чтобы определить `base_path` и API `host` из параметров `default_account`.
        """
        if not self.default_account:
            return

        self.client.set_base_path(self.default_account.base_uri)
        self.client.host = f'{self.default_account.base_uri}/restapi'

    def _get_jwt_token(self, log_error: bool = True) -> OAuthToken:
        """ Получите токен JWT для клиента API для выполнения олицетворенных запросов API.
        Docs:

        https://developers.docusign.com/esign-rest-api/guides/authentication/
        oauth2-jsonwebtoken#step-2-create-a-jwt-token
        
        Аргументы:
            log_error (bool) -
                Должен ли клиент регистрировать ошибки в случае исключения (в некоторых случаях
                когда ожидается обнаруженная ошибка, мы хотим зарегистрировать ее как 
                предупреждение вместо ошибки, чтобы sentry не думал об этом как
                о проблеме.)

        Возвращается:
            (OAuthToken) - подготовленный токен JWT для пользователя
        """
        try:
            jwt_token = self.client.request_jwt_user_token(
                client_id=self.integration_key,
                user_id=self.user_id,
                oauth_host_name=self.oauth_host_name,
                private_key_bytes=self.private_key,
                expires_in=self.token_expiration
            )
            return jwt_token
        except ApiException as e:
            error_msg = f"DocuSign couldn't get JWT token: {e}"
            if log_error:
                logger.error(error_msg)
            else:
                logger.warning(error_msg)
            raise exceptions.GetJWTTokenException

    def _exchange_code_to_access_token(self, code: str) -> OAuthToken:
        """ Преобразуйте `code` в `access_token` для дальнейшего получения пользовательских данных.

        Это требуется в тех случаях, когда мы не знаем DocuSign ID олицетворяемого
        пользователь. Поэтому нам нужно получить его из метода `_get_user_info` позже с помощью
        получено с помощью этого метода `access_token`.

        Атрибуты:
            код (str) - код, возвращаемый после перехода по ссылке из
            `get_consent_link` в браузере (требуется только тогда, когда `user_id` неизвестен)

        Возвращается:
            ((Токен OAuth) - токен доступа для сбора информации о пользователе из DocuSign, когда
            `user_id` неизвестен.
        """
        try:
            token = self.client.generate_access_token(
                client_id=self.integration_key,
                client_secret=self.secret_key,
                code=code,
            )
            return token
        except ApiException as e:
            logger.error(f"DocuSign couldn't get access token: {e}")
            raise exceptions.GetAccessTokenException

    def _get_user_info(self, access_token: str) -> OAuthUserInfo:
        """ Способ получения пользовательских данных от DocuSign после получения его согласия.

        После получения согласия пользователя с помощью метода `get_consent_link`
        необходимо получить руководство пользователя из его данных DocuSign для следующего
        процесс авторизации (`set_access_token`).

        Чтобы получить информацию о пользователе и руководство:
            1. Obtain user Access Token
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-code-grant#step-2-obtain-the-access-token)
            2. Get user info
            (https://developers.docusign.com/esign-rest-api/guides/
            authentication/oauth2-jsonwebtoken#step-4-retrieve-user-account-data)

        Атрибуты:
            access_token (str) - токен доступа, с помощью которого DocuSign возвращает 
            пользователя информация.
        Возвращается:
            ((OAuth userInfo) - сериализованная информация о пользователе

        В качестве пользовательского GUID (уникального идентификатора в DocuSign) следует 
        использовать `sub` поле в возвращаемых данных.
        """
        try:
            user_data = self.client.get_user_info(access_token)
        except ApiException as e:
            logger.error(f"DocuSign couldn't get user info: {e}")
            raise exceptions.GetUserDataException
        return user_data

    def _get_default_account(self, user_info: OAuthUserInfo) -> Account:
        """ Ярлык для получения учетной записи пользователя по умолчанию из всех учетных записей.

        Атрибуты:
            user_info (OAuth userInfo) - объект с информацией о пользователе DocuSign
        Возвращается:
            (Учетная запись) - Объект учетной записи с информацией об учетной записи пользователя 
            по умолчанию
        """
        return next(filter(lambda x: x.is_default, user_info.accounts))

    def _update_token_info(self) -> None:
        """ Ярлык для обновления информации о токене.
        Он добавляет клиенту флаг о том, что токен уже был получен, и
        пересчитывает время истечения его срока действия.
        """
        self.token_received = True
        self.token_expires_timestamp = (
            self._get_current_timestamp() + self.token_expiration
        )

    def _get_current_timestamp(self):
        """ Ярлык для получения текущей временной метки. """
        return int(round(time.time()))


class DocuSignClient(DocuSignImpersonalizedClientMixin):
    """ Клиент для работы с DocuSign SDK.
    Предоставляет все необходимые для DocuSign методы рабочего процесса.
    DocuSign guides: https://developers.docusign.com/esign-rest-api/guides/
    """
    base_path = DS_CONFIG['BASE_PATH']
    oauth_host_name = DS_CONFIG['OAUTH_HOST_NAME']
    integration_key = DS_CONFIG['INTEGRATION_KEY']
    token_expiration = DS_CONFIG['TOKEN_EXPIRATION']
    secret_key = DS_CONFIG['SECRET_KEY']
    private_key = bytes(DS_CONFIG['PRIVATE_RSA_KEY'], 'utf-8')
    draft_envelope_email_subject = DS_CONFIG['DRAFT_ENVELOPE_EMAIL_SUBJECT']

    def __init__(self, *args, **kwargs):
        """Initialize DocuSign API client."""
        super().__init__(*args, **kwargs)
        self.client = docusign.ApiClient(
            base_path=self.base_path,
            oauth_host_name=self.oauth_host_name,
        )

    @property
    def envelope_status_webhook_url(self):
        """ Ярлык для получения `envelope_status_webhook_url`. """
        return f"{settings.BASE_URL}{DS_CONFIG['ENVELOPE_STATUS_WEBHOOK_URL']}"

    @property
    def consent_redirect_url(self):
        """ Ярлык для получения `consent_redirect_url`. """
        return f"{settings.BASE_URL}{DS_CONFIG['CONSENT_REDIRECT_URL']}"

    def create_envelope(
        self, documents: List[Document], recipients: List[Signer],
        email_subject: str = None, is_open: bool = True,
        event_notification: EventNotification = None
    ) -> dict:
        """ Способ создания конверта.
        Этот метод позволяет создавать `draft` конверта или нет:
            - draft - будет создан не готовый к подписанию конверт, который
            не будет отправлено подписчикам по электронной почте, оно просто подождет, пока
            оно будет отредактировано и отправлено подписчикам в режиме редактирования.

            - not draft - создайте готовый к подписанию конверт в DocuSign, который
            будет отправлено подписавшим по электронной почте.

        Атрибуты:
            documents (Document) - список документов в конвертах для подписания
            recipients (signer) - список лиц, подписавших конверт
            email_subject (str) - заголовок электронного письма DocuSign для подписания документов
            is_open (bool) - флаг, должен ли конверт DocuSign быть черновиком или нет
            event_notification (Event Notification) - настройка веб-крючка конверта
                для выполнения обновления его статусов

        Возвращается:
            (dict) - диктант с информацией о созданном конверте
        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # обновите токен, если срок его действия истек
        self.update_token()

        try:
            envelope_definition = EnvelopeDefinition(
                email_subject=email_subject or self.draft_envelope_email_subject,  # noqa
                documents=documents,
                recipients=Recipients(signers=recipients),
                status=self._get_status(is_open),
                event_notification=event_notification
            )

            envelope_api = EnvelopesApi(self.client)
            results = envelope_api.create_envelope(
                account_id=self.default_account.account_id,
                envelope_definition=envelope_definition,
            )
            logger.debug(f'Created new Envelope: {results.envelope_id}')
        except ApiException as e:
            logger.error(f"DocuSign couldn't create envelope: {e}")
            raise exceptions.CreateEnvelopeException

        return results

    def update_envelope(self, envelope_id: str, **kwargs) -> dict:
        """ Обновите существующий конверт новыми параметрами.

        Атрибуты:
            envelope_id (str) - идентификатор обновленного конверта в DocuSign
        Возвращается:
            (dict) - диктант с информацией об обновленном конверте
        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # обновите токен, если срок его действия истек
        self.update_token()

        try:
            envelope_api = EnvelopesApi(self.client)
            results = envelope_api.update(
                account_id=self.default_account.account_id,
                envelope_id=envelope_id,
                **kwargs
            )
            logger.debug(f'Updated envelope: {envelope_id}')
        except ApiException as e:
            logger.error(
                f"DocuSign couldn't update envelope {envelope_id}: {e}"
            )
            raise exceptions.UpdateEnvelopeException

        return results

    def get_envelope_edit_link(
        self, envelope_id: str, return_url: str = '', log_error: bool = True
    ) -> str:
        """ Ярлык для получения ссылки "редактировать" для конверта по его идентификатору.
        Метод генерирует ссылку `редактировать` на DocuSign для уже существующего конверта
        и возвращает его. Эта ссылка может быть открыта только без авторизации
        один раз, поэтому в следующий раз для этого будет постоянно требоваться авторизация 
        пользователя.

        Аргументы:
            envelope_id (str) - идентификатор конверта DocuSign
            return_url (str) - url, на который DocuSign должен перенаправить пользователя
               после редактирования конверта
            log_error (bool) -
                Должен ли клиент регистрировать ошибки в случае исключения (в некоторых случаях
                когда ожидается обнаруженная ошибка, мы хотим зарегистрировать ее как 
                предупреждение вместо ошибки, чтобы sentry не думал об этом как о проблеме.

        Возвращается:
            (str) - сгенерированная ссылка на редактирование конверта в DocuSign
        """
        if not self.is_consent_obtained():
            raise exceptions.UserHasNoConsentException

        # обновите токен, если срок его действия истек
        self.update_token()

        try:
            envelope_api = EnvelopesApi(self.client)
            # не разрешать устанавливать значение None, чтобы не вызывать ошибок BadRequest
            return_url = '' if not return_url else return_url
            edit_url = envelope_api.create_edit_view(
                account_id=self.default_account.account_id,
                envelope_id=envelope_id,
                return_url_request=ReturnUrlRequest(return_url)
            )
        except ApiException as e:
            error_msg = f"DocuSign couldn't create edit view for envelope: {e}"
            if log_error:
                logger.error(error_msg)
            else:
                logger.warning(error_msg)

            # если в ошибке присутствует код `ENVELOPE_DOES_NOT_EXIST` - поднимите
            # `NoEnvelopeExistsException`
            if 'ENVELOPE_DOES_NOT_EXIST' in str(e):
                raise exceptions.NoEnvelopeExistsException
            # в противном случае поднимите `CreateEditEnvelopeViewException`
            raise exceptions.CreateEditEnvelopeViewException

        return edit_url.url

    def _get_status(self, is_open: bool = True) -> str:
        """ Ярлык для получения "статуса" для конверта в зависимости от параметра `is_open`.
        """
        return ENVELOPE_STATUS_CREATED if is_open else ENVELOPE_STATUS_SENT
