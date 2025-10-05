import os
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.transaction import non_atomic_requests
from django.http.response import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from allauth.account import app_settings
from allauth.account import views as account_views
from allauth.account.models import EmailAddress
from constance import config
from rest_auth import views
from rest_auth.registration import views as reg_views
from twilio.rest import Client
from apps.core.api.views import UserAgentLoggingMixin
from apps.users.models.users import AppUser
from ... import utils
from ...api import serializers
from .utils.verification import resend_email_confirmation


@method_decorator(non_atomic_requests, name='dispatch')
class AppUserLoginView(UserAgentLoggingMixin, views.LoginView):
    """ Конечная точка авторизации.
    По умолчанию `LoginView` отправляет сигнал `user_logged_in` только тогда, когда
    `REST_SESSION_LOGIN == True` (который позволяет входить в сеанс в Login DRF API
    просмотр), но при установке этого параметра возникают проблемы с защитой CSRF.

    Таким образом, эта настройка отключена, и сигнал `user_logged_in` отправляется в пользовательском режиме
    `AppUserLoginView`, чтобы установить для пользователя `last_login`.

    Неатомные транзакции позволяют сохранять неудачные попытки входа в систему. Сбой входа в систему
    попытки возвращают `HTTP 400`, а атомарные транзакции не позволяют сохранить
    данные после ошибок.
    """
    serializer_class = serializers.AppUserLoginSerializer

    def login(self):
        """Send signal `user_logged_in` on API login."""
        super().login()

        user_logged_in.send(
            sender=self.user.__class__,
            request=self.request,
            user=self.user
        )

    def post(self, *args, **kwargs):
        """Authorization endpoint.

        On successful authentication returns token(
            `key`,
            `user_type`,
            `user_id`,
            `plan_id`
        ).

        """
        try:
            return super().post(*args, **kwargs)
        except EmailAddress.DoesNotExist:
            message = "The email you entered isn’t connected to an account"
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "success": False,
                    "message": message
                }
            )
        except NotAuthenticated:
            msg = (
                'You will be able to login after'
                ' your application gets approved'
            )
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "message": msg
                }
            )


class ValidateCredentialView(UserAgentLoggingMixin, views.LoginView):
    serializer_class = serializers.AppUserLoginValidationSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            if data['user'] is not None:
                return Response(
                    status=status.HTTP_200_OK,
                    data={'success': True}
                )
            else:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'success': False,
                        'detail': 'User does not exist with these credentials'
                    }
                )
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'success': False,
                    'detail': str(e)
                }
            )


class LogoutView(UserAgentLoggingMixin, views.LogoutView):
    """Logout user from app.

    Accepts only post request. Returns the success message.
    """
    http_method_names = ('post',)


class PasswordChangeView(UserAgentLoggingMixin, views.PasswordChangeView):
    """Change user's password.

    Accepts the following POST parameters:
        old_password
        new_password1
        new_password2
    Returns the success/fail message.

    """


class PasswordResetView(UserAgentLoggingMixin, views.PasswordResetView):
    """Reset user's password.

    This endpoint send to user with url for resetting password, at the end of
    which is data for resetting the password.
    Example `1-5b2-e2c1ce64d63673f0e78f`, where:
        `1` - is `uid` or user id
        `5b2-e2c1ce64d63673f0e78f` - `token` for resetting password

    """


class PasswordResetConfirmView(UserAgentLoggingMixin,
                               views.PasswordResetConfirmView):
    """Change user's password on reset.

    This endpoint confirms the reset of user's password.

    Explanation of token and uid
    Example `1-5b2-e2c1ce64d63673f0e78f`, where:
        `1` - is `uid` or user id
        `5b2-e2c1ce64d63673f0e78f` - `token` for resetting password

    """


class VerifyEmailView(UserAgentLoggingMixin, reg_views.VerifyEmailView):
    """ Подтвердите адрес электронной почты пользователя
    Эта конечная точка подтверждает адрес электронной почты с помощью "ключа" 
    ссылки для подтверждения
    """


class VerifyConfirmEmailRedirectView(UserAgentLoggingMixin,
                                     account_views.ConfirmEmailView):
    """ Перенаправление на страницу с ошибкой проверки электронной почты """
    url = config.PROD_FRONTEND_LINK

    def get_redirect_url(self):
        from ... import notifications
        from ....users.models import AppUser 
        user = AppUser.objects.filter(email=self.get_object().email_address).first()
        notifications.RegisterUserNotification(user).send()
        return 'https://app.justmediationhub.com/auth/email-verified?success=true'

    def get(self, *args, **kwargs):
        try:
            self.object = self.get_object()
            if app_settings.CONFIRM_EMAIL_ON_GET:
                return self.post(*args, **kwargs)
        except Http404:
            self.object = None
        return redirect(
            'https://app.justmediationhub.com/auth/email-verified?success=false'
        )


class ResendEmailConfirmation(UserAgentLoggingMixin, views.APIView):

    """ Повторно отправьте пользователю ссылку для подтверждения по электронной почте """

    def post(self, request):
        try:
            email = request.data['email']
            user = AppUser.objects.get(email__iexact=email)
            resend_email_confirmation(request, user, True)
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "detail": "Resend verification successfully"
                }
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "detail": "Not resend verification successfully"
                }
            )


class VerifyCodeView(UserAgentLoggingMixin, views.APIView):

    """Verify Code for Two FA authentication"""

    def post(self, request):
        try:
            phone = utils.format_phone_for_twillio(request.data['phone'])
            code = request.data['code']
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service = settings.TWILIO_SERVICE
            client = Client(account_sid, auth_token)

            verification_check = client.verify.services(service)\
                .verification_checks.create(to=phone, code=code)
            return Response(
                status=status.HTTP_200_OK,
                data={
                    "success": verification_check.valid
                }
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False
                }
            )


class SyncPlanView(UserAgentLoggingMixin, views.APIView):

    def get(self, request):
        from django.core import management
        management.call_command('djstripe_sync_plans_from_stripe', verbosity=0)
        return Response(
            status=status.HTTP_200_OK,
            data={
                "detail": "Sync plan successfully!"
            }
        )
