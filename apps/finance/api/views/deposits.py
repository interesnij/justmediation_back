import logging
import os
import uuid
from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
import stripe
from constance import config
from libs.api.serializers.serializers import URLSerializer
from apps.core.api.views import BaseViewSet
from apps.users.api.permissions import IsMediatorHasActiveSubscription
from apps.users.models import AppUser
from ...models import AccountProxy, FinanceProfile
from ...services import stripe_deposits_service
from ..permissions import IsMediatorHasNoConnectedAccount
from ..serializers import (
    AccountProxySerializer,
    ErrorCallbackSerializer,
    SuccessCallbackSerializer,
)

__all__ = (
    'AccountAuthViewSet',
    'CurrentAccountViewSet',
)


logger = logging.getLogger('stripe')

class AccountAuthViewSet(BaseViewSet):
    """ Просмотр, установленный для настройки учетных записей stripe 
    для прямых депозитов адвоката.

    Чтобы сделать доступными прямые платежи какому-либо адвокату, ему необходимо создать
    учетная запись stripe `Express` через наше приложение, заполните необходимые для stripe поля
    и ждать, пока его информация не будет подтверждена stripe.

    Это представление предоставляет возможность создать учетную запись stripe `Express`
    создание и обработка обратного вызова stripe после регистрации пользователя.

    Документы экспресс-аккаунта:
        https://stripe.com/docs/connect/express-accounts
    Весь процесс регистрации учетной записи:
        https://stripe.com/docs/connect/collect-then-transfer-guide
    """
    base_filter_backends = None
    pagination_class = None
    permissions_map = {
        'get_authorization_link': (
            IsAuthenticated,
            IsMediatorHasActiveSubscription,
            IsMediatorHasNoConnectedAccount
        ),
        'process_auth_callback': (AllowAny,)
    }

    @action(methods=['GET'], detail=False, url_path='url')
    def get_authorization_link(self, request, *args, **kwargs):
        """ Метод API для получения URL-адреса авторизации учетной записи `Express` для адвоката
        Возвращенный URL-адрес позволяет зарегистрировать новую учетную запись "Express" или 
        авторизовать существующую. Также он подготавливает `state_token` для пользователя, 
        чтобы сопоставить его позже при обратном вызове.
        Также этот метод выдает ошибку "403" в случае, если пользователь с существующим
        подключенный `аккаунт` пытается получить ссылку для создания нового.
        """
        # serializer = SuccessErrorUrlRequestSerializer(data=request.query_params)  # noqa
        # serializer.is_valid(raise_exception=True)

        state = str(uuid.uuid4())
        auth_url = stripe_deposits_service.get_authorization_url(
            state=state, user=request.user
        )
        # запомните случайное "состояние", чтобы обеспечить дальнейшее совпадение 
        # пользователей в Stripe authorize обратный вызов + запомнить `success_url` и 
        # `error_url` для какого пользователя будет перенаправлен на дальнейшие шаги авторизации
        # cache.set(
        #     state, {
        #         'user_id': request.user.id,
        #         'success_url': serializer.validated_data['success_url'],
        #         'error_url': serializer.validated_data['error_url']
        #     },
        #     60 * 60 * 24  # 1 day
        # )
        return response.Response(
            data=URLSerializer({'url': auth_url}).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='callback')
    def process_auth_callback(self, request, *args, **kwargs):
        """ Метод API для обработки перенаправления OAuth Stripe connect.
        Этот метод обрабатывает возвращенные "состояние" и `код`, обменивает их на
        созданный идентификатор учетной записи и токен доступа, создает новую учетную запись 
        stripe экземпляр в базе данных и связывает его с `пользователем` из параметров кэша.
        """
        data = request.query_params
        success = 'error' not in data
        serializer = (
            SuccessCallbackSerializer(data=data) if success else
            ErrorCallbackSerializer(data=data)
        )
        is_valid = serializer.is_valid(raise_exception=False)

        state_info = cache.get(data.get('state'), {})
        error_return_url = state_info.get('error_url')
        success_return_url = state_info.get('success_url')
        user = AppUser.objects.filter(id=state_info.get('user_id')).first()

        # перенаправить на соответствующую страницу, если произошла ошибка
        if not is_valid or not success or not state_info or not user:
            error_return_url = error_return_url or \
                settings.STRIPE_BASE_AUTH_ERROR_REDIRECT_URL
            return response.Response(
                headers={'Location': error_return_url},
                status=status.HTTP_302_FOUND
            )

        try:
            # не разрешить создавать новую учетную запись для пользователя с существующей учетной записью
            if user.finance_profile.deposit_account is not None:
                raise AttributeError(
                    f'User {user} already has deposit account'
                )

            # попробуйте обменять возвращенный код на auth `token`
            token_data = stripe_deposits_service.get_token(data['code'])
            # сохраните подключенную учетную запись в базе данных и свяжите ее с пользователем
            account = AccountProxy.get_connected_account_from_token(
                access_token=token_data['access_token']
            )
            user.finance_profile.deposit_account = account
            user.finance_profile.save()
            # выполните повторную синхронизацию учетной записи, чтобы получить фактические 
            # данные и уведомить пользователя
            account = AccountProxy.resync(account.id)
            account.notify_user()

        # регистрировать предупреждение только в том случае, если у пользователя нет 
        # `finance_profile` или "депозитный счет" уже существует
        except (AttributeError, FinanceProfile.DoesNotExist) as e:
            return self._process_auth_callback_error(
                e, user, error_return_url, False
            )

        # ошибка log, когда не удалось получить `токен` или `учетную запись` от stripe
        except Exception as e:
            return self._process_auth_callback_error(
                e, user, error_return_url, False
            )

        return response.Response(
            headers={'Location': success_return_url},
            status=status.HTTP_302_FOUND
        )

    def _process_auth_callback_error(
        self, error: Exception, user: AppUser, error_return_url: str,
        log_error=True,
    ) -> response.Response:
        """ Ошибки обработки, появившиеся при try/catch `process_auth_callback`.

        Аргументы:
            error (Exception): возникает при ошибке блока try/catch
            error_return_url (str): url-адрес ошибки, на который должен быть возвращен пользователь
            user (AppUser): пользователь приложения, для которого обрабатывается обратный вызов
            log_error (bool): флаг, который определяет, должна ли ошибка
                регистрироваться как `error` or `warning`
        """
        log_method = logger.error if log_error else logger.warning
        log_method(
            f"Couldn't create connected account for user {user.id}: {error}"
        )
        return response.Response(
            headers={'Location': f'{error_return_url}?error={error}'},
            status=status.HTTP_302_FOUND
        )


class CurrentAccountViewSet(BaseViewSet):
    """ Просмотр, установленный для получения учетной записи прямого пополнения 
    счета пользователя и ссылки для входа в систему.
    """
    base_filter_backends = None
    pagination_class = None

    serializer_class = AccountProxySerializer
    permission_classes = IsAuthenticated, IsMediatorHasActiveSubscription

    def get_object(self):
        """ Переопределен метод возврата учетной записи пользователя из `finance_profile`.
        """
        finance_profile = getattr(self.request.user, 'finance_profile', None)
        account = getattr(finance_profile, 'deposit_account', None)
        if not account:
            raise Http404
        return account

    @action(methods=['GET'], detail=False, url_path='current')
    def get_current(self, request, *args, **kwargs):
        """ Пользовательский метод для получения текущей учетной записи пользователя 
        без параметра `id`.

        То же, что и оригинальная реализация DRF `retrieve`, но без `id`
        параметр в пути.

        Stripe Docs: https://stripe.com/docs/api/accounts/object

        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return response.Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='current/login-url')
    def get_login_link(self, request, *args, **kwargs):
        """ API-метод для получения ссылки для входа в панель управления учетной 
        записью Express в Stripe.

        Stripe docs: https://stripe.com/docs/connect/express-dashboard

        """
        account = self.get_object()
        return response.Response(
            data=URLSerializer({'url': account.login_url}).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False, url_path='current/onboarding-url')
    def get_onboarding_link(self, request, *args, **kwargs):
        """ API-метод для получения ссылки на панель управления учетной 
        записью Express в Stripe.

        Stripe docs: https://stripe.com/docs/connect/express-dashboard

        """
        user = request.user

        finance_profile = FinanceProfile.objects.filter(
            user=user,
            deposit_account__isnull=False
        ).first()
        if finance_profile:
            account_id = finance_profile.deposit_account.id
        else:
            account = stripe.Account.create(
                type='express',
                country='US',
                email=user.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )
            account_id = account.id
            stripe_account = AccountProxy().resync(account_id)
            finance_profile = FinanceProfile.objects.filter(
                user=user
            ).first()
            finance_profile.deposit_account = stripe_account
            finance_profile.save()
            
        current_site = config.PROD_FRONTEND_LINK

        account_link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=f"{current_site}mediator/bank",
            return_url=f"{current_site}mediator/bank",
            type="account_onboarding",
        )
        return response.Response(
            data=URLSerializer({'url': account_link.url}).data,
            status=status.HTTP_200_OK
        )
