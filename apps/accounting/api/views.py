import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from intuitlib.exceptions import AuthClientError
from libs.api.serializers.serializers import (
    SuccessErrorUrlRequestSerializer,
    URLSerializer,
)
from libs.quickbooks import default_quickbooks_client as quickbooks_client
from apps.core.api.views import BaseViewSet
from apps.users.api.permissions import IsMediatorHasActiveSubscription
from .. import services
from . import serializers


logger = logging.getLogger('quickbooks')

CACHE_QB_AUTH_KEY = 'qb_auth'


class QuickBooksAuthorizationView(BaseViewSet):
    """Просмотр различных операций авторизации QuickBooks.
    Рабочий процесс QuickBooks OAuth2: https://developer.intuit.com/app/developer/
    qbo/docs/разработка/аутентификация и авторизация/oauth-2.0
    """
    base_filter_backends = None
    pagination_class = None
    permissions_map = {
        'default': (IsAuthenticated, IsMediatorHasActiveSubscription),
        'process_auth_callback': (AllowAny,)
    }

    @action(methods=['GET'], url_path='url', detail=False)
    def get_authorization_url(self, request, *args, **kwargs):
        """Метод API для получения URL-адреса авторизации QuickBooks для адвоката.
        Он подготавливает `state_token` для пользователя и запоминает успех и ошибку
        перенаправляет в кэше.
        """
        serializer = SuccessErrorUrlRequestSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        client = quickbooks_client()
        auth_url = client.get_authorization_url()
        # # запомните случайный `state_token`, сгенерированный клиентом Quickbooks, чтобы сделать
        # дальнейшее совпадение пользователя в обратном вызове QB auth + запомните `success_url` и
        # `error_url`, на который пользователь будет перенаправлен на дальнейших этапах авторизации
        cache.set(
            client.auth_client.state_token, {
                'user_id': request.user.id,
                'success_url': serializer.validated_data['success_url'],
                'error_url': serializer.validated_data['error_url']
            },
            60 * 60 * 24  # 1 day
        )
        return Response(
            data=URLSerializer({'url': auth_url}).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], url_path='callback', detail=False)
    def process_auth_callback(self, request, *args, **kwargs):
        """Метод API, который обрабатывает обратный вызов QuickBook OAuth2.
        Этот обратный вызов запускается QuickBooks после того, как пользователь одобряет /отклоняет
        запрос на доступ к приложению. Таким образом, в зависимости от действий пользователя ответ может быть:
        
        - успешно -> продолжить аутентификацию и перенаправить пользователя на `success_url`
        - ошибка -> перенаправить пользователя на `error_url`
        - отсутствует `state_token` -> перенаправить пользователя на
        
        `BASE_AUTH_ERROR_REDIRECT_URL`
        """
        data = request.query_params

        if 'error' in data:
            serializer = serializers.AccessDeniedSerializer(data=data)
            success = False
        else:
            serializer = serializers.AccessAllowedSerializer(data=data)
            success = True

        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        state_info = cache.get(data['state'])

        # верните пользователя на соответствующую страницу, если произошла ошибка
        if not state_info or not success:
            return_url = state_info['error_url'] if state_info \
                else settings.QUICKBOOKS['BASE_AUTH_ERROR_REDIRECT_URL']
            return Response(
                headers={'Location': return_url},
                status=status.HTTP_302_FOUND
            )

        # получите токены авторизации пользователя для выполнения запросов функций и
        # сохраните их в кэше на 1 день - если авторизация пользователя прошла успешно
        return_url = state_info['success_url']
        try:
            auth_info = quickbooks_client().get_bearer_token(
                auth_code=data['code'],
                realm_id=data['realmId']
            )
            cache.set(
                state_info['user_id'],
                {CACHE_QB_AUTH_KEY: auth_info},
                60 * 60 * 24
            )
        except AuthClientError:
            return_url = state_info['error_url']

        return Response(
            headers={'Location': return_url},
            status=status.HTTP_302_FOUND
        )


class QuickBooksExportView(BaseViewSet):
    """Просмотр различных операций экспорта QuickBooks."""
    base_filter_backends = None
    pagination_class = None
    permission_classes = IsAuthenticated, IsMediatorHasActiveSubscription
    serializer_class = serializers.CustomerSerializer
    serializers_map = {
        'get_customers': serializers.CustomerSerializer,
        'export': serializers.ExportInvoiceSerializer,
    }

    @action(methods=['GET'], url_path='customers', detail=False)
    def get_customers(self, request, *args, **kwargs):
        """Получите все доступные для экспорта пользовательские "клиенты` из QuickBooks."""
        client = self._get_quickbooks_client(request)
        customers = [customer.to_dict() for customer in client.get_customers()]
        serializer = self.get_serializer_class()(customers, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], url_path='invoice', detail=False)
    def export(self, request, *args, **kwargs):
        """Инициируйте экспорт счета-фактуры в QuickBooks."""
        client = self._get_quickbooks_client(request)

        # проверка параметров запроса на экспорт
        serializer = self.get_serializer(
            data=request.data, qb_api_client=client
        )
        serializer.is_valid(raise_exception=True)

        # экспорт счета-фактуры в QuickBooks
        invoice = serializer.validated_data['invoice']
        customer = serializer.validated_data.get('customer')
        if not customer:
            customer = services.create_customer(invoice.matter.client, client)
        services.create_or_update_invoice(invoice, customer, client)

        return Response(status=status.HTTP_200_OK)

    def _get_quickbooks_client(self, request):
        """Ярлык для получения инициализированного клиента QuickBooks."""
        auth_tokens = cache.get(request.user.id, {}).get(CACHE_QB_AUTH_KEY, {})
        return quickbooks_client(**auth_tokens, user=request.user)
