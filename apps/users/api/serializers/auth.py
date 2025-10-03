from django.conf import settings
from django.contrib.auth import get_user_model, password_validation
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, ValidationError
from allauth.account import app_settings
from allauth.account.forms import default_token_generator
from rest_auth import serializers as auth_serializers
from rest_auth.registration.serializers import RegisterSerializer
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from apps.users.models import AppUser
from ... import utils
from ..serializers import auth_forms
from .extra import TimezoneSerializer


class RemoveUsernameFieldMixin:
    """ Удаляет имя пользователя ."""

    def get_fields(self):
        """Remove 'username' from fields."""
        fields = super().get_fields()
        del fields['username']
        return fields


class AppUserLoginSerializer(
    RemoveUsernameFieldMixin,
    auth_serializers.LoginSerializer
):
    """LoginSerializer без имени пользователя."""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        password = attrs.get('password')
        code = attrs.get('code')

        user = None

        if email and password:
            user = User.objects.filter(email__iexact=email).first()
        if user and not user.is_active:
            msg = 'This user\'s application is still pending'
            raise NotAuthenticated(msg)

        user = self._validate_email(email, password)

        if user is None:
            msg = _('Wrong credentials')
            raise ValidationError(msg)

        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            if app_settings.EMAIL_VERIFICATION == \
                    app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise ValidationError(_('E-mail is not verified.'))

        if user.twofa and user.phone:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service = settings.TWILIO_SERVICE
            try:
                client = Client(account_sid, auth_token)
                phone = utils.format_phone_for_twillio(user.phone)

                verification_check = client.verify.services(service)\
                    .verification_checks.create(to=phone, code=code)
                if not verification_check.valid:
                    raise ValidationError(_('The code is incorrect'))
            except TwilioRestException:
                raise ValidationError(_('The code is incorrect'))

        attrs['user'] = user
        return attrs


class AppUserLoginValidationSerializer(
    RemoveUsernameFieldMixin,
    auth_serializers.LoginSerializer
):
    """LoginSerializer without username field."""
    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if email and password:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            raise NotAuthenticated(_('Wrong credentials'))

        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            if app_settings.EMAIL_VERIFICATION == \
                    app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise NotAuthenticated(_('E-mail is not verified.'))

        if user and not user.is_active:
            msg = 'This user\'s application is still pending'
            raise NotAuthenticated(msg)

        user = self._validate_email(email, password)

        attrs['user'] = user
        return attrs


class AppUserRelatedRegisterSerializerMixin(RegisterSerializer):
    """ Сериализатор mixin для регистрации адвоката и клиента.
    Этот набор сериализаторов содержит общие поля и логику, необходимые для
    регистрации адвоката и клиента.
    """

    def get_cleaned_data(self):
        """ Сохраняйте дополнительные данные во время вызова регистрационного API.
        Также очистите validated_data от регистрационных данных (электронной почты и паролей).
        Если вы добавите дополнительные данные, не забудьте обновить AccountAdapter.
        """
        cleaned_data = super().get_cleaned_data()
        user_data = self.validated_data.pop('user', {})
        self.validated_data.pop('password1')
        self.validated_data.pop('password2')
        email = self.validated_data.pop('email')

        cleaned_data.update({
            'email': email,
            'first_name': user_data['first_name'],
            'middle_name': user_data.get('middle_name', None),
            'last_name': user_data['last_name'],
            'phone': user_data['phone'],
            'avatar': user_data.get('avatar', []),
            'specialities': user_data.get('specialities', []),
        })
        return cleaned_data

    def save(self, request):
        """ Создайте соответствующий профиль для нового пользователя и задайте специализации. """
        try:
            user = super().save(request)
        except IntegrityError:
            # Это произойдет, когда мы попытаемся зарегистрировать нескольких пользователей 
            # с помощью одно и то же электронное письмо в одно и то же время
            raise ValidationError(
                dict(
                    email=(
                        'A user is already registered with '
                        'this e-mail address.'
                    )
                )
            )
        user.specialities.set(self.cleaned_data['specialities'])
        self.create_related(user)
        return user

    def create_related(self, user):
        """ Создайте запись, связанную с пользователем (адвокатом или клиентом). """
        raise NotImplementedError('Implement logic of creation!')


class AppUserPasswordResetSerializer(auth_serializers.PasswordResetSerializer):
    """ Представление для сброса пароля. """
    password_reset_form_class = auth_forms.ResetPasswordForm

    def validate_email(self, email):
        """ Проверьте, что адрес электронной почты присвоен пользователю. """
        self.reset_form = self.password_reset_form_class(
            data=self.initial_data
        )
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(
                'The e-mail address is not assigned to any user account'
            )
        return email


class AppUserPasswordResetConfirmSerializer(
    auth_serializers.PasswordResetConfirmSerializer
):
    """ Пользовательский сброс пароля подтверждает сериализатор. """

    TOKEN_ERROR_MESSAGE = 'Token is expired or incorrect. ' \
                          'Try resetting password once again.'

    def validate(self, attrs):
        """ Проверьте экземпляр пользователя.
        Этот метод идентичен исходному методу `validate`, но без
        проверка формата `uid`, поскольку идентификатор модели `User` не является uuid.
        Также он использует all_auth default_token_generator вместо django
        значение по умолчанию одно.
        """
        User = get_user_model()
        self._errors = {}

        try:
            # Удалена проверка формата uid в этой строке
            self.user = User.objects.get(pk=attrs['uid'])
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'uid': [self.TOKEN_ERROR_MESSAGE]})

        self.custom_validation(attrs)
        # Создайте экземпляр SetPasswordForm
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        # Мы используем default_token_generator из пакета all_auth
        if not default_token_generator.check_token(
            self.user, attrs['token']
        ):
            raise ValidationError({'token': [self.TOKEN_ERROR_MESSAGE]})

        return attrs


class TokenSerializer(auth_serializers.TokenSerializer):
    """ Переопределен сериализатор токенов по умолчанию.
        В нем есть `user_type`, чтобы интерфейсная команда могла понять, 
        с кем они имеют дело.
    """
    user_type = serializers.ChoiceField(
        source='user.user_type',
        choices=AppUser.USER_TYPES
    ) 

    avatar = serializers.CharField(
        source='user.avatar'
    )

    user_id = serializers.CharField(
        source='user.pk'
    )

    plan_id = serializers.CharField(
        source='user.plan_id'
    )

    phone = serializers.CharField(
        source='user.phone'
    )

    onboarding = serializers.BooleanField(
        source='user.onboarding'
    )

    timezone_data = TimezoneSerializer(
        source='user.timezone'
    )
    is_free_subscription = serializers.BooleanField(
        source='user.is_free_subscription'
    )

    owned_enterprise = serializers.SerializerMethodField()
    enterprise = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    middle_name = serializers.CharField(source='user.middle_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta(auth_serializers.TokenSerializer.Meta):
        fields = (
            'key',
            'user_type',
            'avatar',
            'user_id',
            'plan_id',
            'onboarding',
            'phone',
            'timezone_data',
            'owned_enterprise',
            'enterprise',
            'role',
            'email',
            'first_name',
            'middle_name',
            'last_name',
            'is_free_subscription',
        )

    def get_owned_enterprise(self, obj):
        from apps.users.api.serializers import EnterpriseAndAdminUserSerializer
        return EnterpriseAndAdminUserSerializer(
            obj.user.owned_enterprise
        ).data if hasattr(obj.user, 'owned_enterprise') else None

    def get_enterprise(self, obj):
        from apps.users.api.serializers import EnterpriseAndAdminUserSerializer
        if hasattr(obj.user, 'mediator') and obj.user.mediator.enterprise:
            return EnterpriseAndAdminUserSerializer(
                obj.user.mediator.enterprise
            ).data
        return None

    def get_role(self, obj):
        return obj.user.owned_enterprise.role \
            if hasattr(obj.user, 'owned_enterprise') else ''


class AppUserPasswordChangeSerializer(
    auth_serializers.PasswordChangeSerializer
):
    """ Переопределено для проверки пароля 1 перед установкой passwordform full_clean. """

    def validate_new_password1(self, password):
        """Validate new password."""
        password_validation.validate_password(password, self.user)
        return password
