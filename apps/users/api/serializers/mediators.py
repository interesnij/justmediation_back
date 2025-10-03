from django.core.validators import MaxValueValidator
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ....core.api.serializers import BaseSerializer
from ....finance.models import FinanceProfile, PlanProxy
from ... import models
from ...models import Enterprise, EnterpriseMembers
from .mediator_links import MediatorEducationSerializer
from .auth import AppUserRelatedRegisterSerializerMixin
from .enterprise import EnterpriseAndAdminUserSerializer, EnterpriseSerializer
from .extra import (
    AppointmentTypeSerializer,
    CurrenciesSerializer,
    FeeKindSerializer,
    FirmLocationSerializer,
    JurisdictionsSerializer,
    LanguageSerializer,
    PaymentTypeSerializer,
    TimezoneSerializer,
)
from .user import AppUserRelatedSerializerMixin


class MediatorSerializer(AppUserRelatedSerializerMixin, BaseSerializer):
    """Serializer for Mediator model."""

    type = serializers.CharField(source='user.user_type', read_only=True)
    education = MediatorEducationSerializer(many=True, allow_empty=False)
    distance = serializers.FloatField(
        default=None,
        source='distance.m',
        label='Distance to mediator in meters',
        read_only=True
    )

    fee_types_data = FeeKindSerializer(
        source='fee_types', many=True, read_only=True
    )

    practice_jurisdictions = JurisdictionsSerializer(
        many=True, required=False
    )

    firm_locations = FirmLocationSerializer(
        many=True, required=False
    )

    appointment_type_data = AppointmentTypeSerializer(
        source='appointment_type', many=True, read_only=True
    )
    payment_type_data = PaymentTypeSerializer(
        source='payment_type', many=True, read_only=True
    )
    spoken_language_data = LanguageSerializer(
        source='spoken_language', many=True, read_only=True
    )
    fee_currency_data = CurrenciesSerializer(
        source='fee_currency', read_only=True
    )
    is_verified = serializers.ReadOnlyField()
    has_active_subscription = serializers.ReadOnlyField(
        source='user.has_active_subscription'
    )
    timezone = serializers.PrimaryKeyRelatedField(
        source='user.timezone',
        queryset=models.TimeZone.objects.all(),
        required=False
    )
    timezone_data = TimezoneSerializer(source='user.timezone', read_only=True)
    enterprise = EnterpriseSerializer('enterprise', read_only=True)
    avatar = serializers.CharField(source='user.avatar', required=False)
    owned_enterprise = EnterpriseSerializer(
        source='user.owned_enterprise', read_only=True, default=None
    )
    years_of_experience = serializers.IntegerField(validators=(
            MaxValueValidator(
                100,
                'Please make sure the Years of Experience value is less than '
                '%(limit_value)s'
            ),
        ), required=False
    )

    class Meta:
        model = models.Mediator
        fields = (
            'id',
            'distance',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'type',
            'avatar',
            'biography',
            'firm_name',
            'website',
            'firm_locations',
            'is_verified',
            'has_active_subscription',
            'verification_status',
            'featured',
            'sponsored',
            'sponsor_link',
            'followers',
            'education',
            'practice_jurisdictions',
            'practice_description',
            'years_of_experience',
            'have_speciality',
            'specialities',
            'specialities_data',
            'speciality_time',
            'speciality_matters_count',
            'fee_rate',
            'fee_types',
            'extra_info',
            'charity_organizations',
            'fee_types_data',
            'keywords',
            'is_submittable_potential',
            #'attachment', # всесто registration_attachments
            'registration_attachments',
            'appointment_type',
            'payment_type',
            'spoken_language',
            'appointment_type_data',
            'payment_type_data',
            'spoken_language_data',
            'fee_currency',
            'fee_currency_data',
            'tax_rate',
            'timezone',
            'timezone_data',
            'enterprise',
            'owned_enterprise',
        )
        read_only_fields = (
            'user',
            'verification_status',
            'featured',
            'sponsored',
            'sponsor_link',
            'followers',
        )
        relations = (
            'user',
            'education',
            'specialities',
            'fee_types',
            'firm_locations',
            'practice_jurisdictions',
            'registration_attachments',
            'appointment_type',
            'payment_type',
            'spoken_language',
            'fee_currency'
        )
        extra_kwargs = {
            'years_of_experience': {
                'required': True
            },
            'keywords': {
                'child': serializers.CharField(),
                'allow_empty': True,
                'required': False,
            }
        }

    @property
    def errors(self):
        """ Сделайте ошибку "education" как ошибку для одного экземпляра.
        Запрос oт интерфейсной команды.
        """
        errors = super().errors
        return errors

    def get_fields_to_hide(self, instance: models.Mediator) -> tuple:
        """ Скрыть registration_attachments от других пользователей. """
        fields_to_hide = super().get_fields_to_hide(instance)
        user = self.user
        if user and user.pk != instance.pk:
            return fields_to_hide + ('registration_attachments',)
        return fields_to_hide


class MediatorDetailSerializer(MediatorSerializer):
    """ Добавлено свойство twofa в  сериализатор Mediator """

    twofa = serializers.BooleanField(source='user.twofa', required=False)
    subscribed = serializers.BooleanField(
        source='user.subscribed',
        read_only=True
    )

    expiration_date = serializers.DateTimeField(
        source='user.expiration_date',
        read_only=True
    )

    class Meta(MediatorSerializer.Meta):
        fields = MediatorSerializer.Meta.fields + (
            'twofa',
            'subscribed',
            'expiration_date'
        )


class CurrentMediatorSerializer(MediatorDetailSerializer):
    """ Добавлено свойство enterprise invite в сериализатор сведений об адвокате """

    enterprise = EnterpriseAndAdminUserSerializer('enterprise', read_only=True)
    enterprises_pending = EnterpriseAndAdminUserSerializer(
        source='user.enterprises_pending',
        many=True,
        read_only=True
    )

    class Meta(MediatorDetailSerializer.Meta):
        fields = MediatorDetailSerializer.Meta.fields + (
            'enterprises_pending',
        )


class MediatorShortSerializer(MediatorSerializer):
    """ Сокращенная версия сериализатора Mediator. """
    is_mediator = serializers.ReadOnlyField(source='user.is_mediator')
    avatar = serializers.CharField(source='user.avatar', required=False)

    class Meta:
        model = models.Mediator
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'avatar',
            'is_verified',
            'verification_status',
            'featured',
            'sponsored',
            'has_active_subscription',
            'specialities',
            'is_mediator',
        )


class MediatorOverviewSerializer(MediatorSerializer):
    """ Сериализует ограниченные сведения об адвокате для общего обзора вопроса """
    avatar = serializers.CharField(source='user.avatar', required=False)
    class Meta:
        model = models.Mediator
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'avatar',
        )


class UpdateMediatorSerializer(CurrentMediatorSerializer):
    """Update Serializer for Mediator model."""
    email = serializers.EmailField(
        source='user.email', read_only=True
    )
    #enterprise = serializers.PrimaryKeyRelatedField(
    #    queryset=Enterprise.objects.all(),
    #    allow_null=True
    #)
    enterprise_data = EnterpriseSerializer(source='user.mediator.enterprise')

    class Meta(CurrentMediatorSerializer.Meta):
        fields = CurrentMediatorSerializer.Meta.fields + ('enterprise_data',)

    def validate_enterprise(self, enterprise):
        if enterprise:
            e_int = enterprise.id
            request = self.context.get('request')
            if not EnterpriseMembers.objects.filter(
                Q(enterprise=e_int, user=request.user) |
                Q(enterprise=e_int, invitee__email=request.user.email)
            ).exists():
                raise serializers.ValidationError(
                    "You can't join to that enterprise "
                    "because you are not invited to it")
        return enterprise

    def update(self, mediator, validated_data):
        """ Обновите запись об адвокате.
        Сначала отношения, указанные пользователем, и после этого мы обновляем пользователя
        и адвокатские поля.
        """

        if 'fee_types' in validated_data:
            fee_types = validated_data.pop('fee_types')
            mediator.fee_types.set(fee_types)

        if 'practice_jurisdictions' in validated_data:
            practice_jurisdictions = validated_data.pop(
                'practice_jurisdictions', []
            )
            self.update_practice_jurisdictions(
                mediator, practice_jurisdictions
            )

        if 'registration_attachments' in validated_data:
            registration_attachments = validated_data.pop(
                'registration_attachments', []
            )
            self.update_registration_attachments(
                mediator, registration_attachments
            )

        if 'education' in validated_data:
            education = validated_data.pop('education', [])
            self.update_education(mediator, education)

        if 'firm_locations' in validated_data:
            firm_locations = validated_data.pop('firm_locations', [])
            self.update_firm_locations(mediator, firm_locations)

        if 'enterprise' in validated_data:
            e_dict = validated_data['enterprise']
            e_int = e_dict.id
            EnterpriseMembers.objects.filter(
                enterprise=e_int,
                user=mediator.user
            ).update(state=EnterpriseMembers.STATE_ACTIVE)
            EnterpriseMembers.objects.filter(
                enterprise=e_int,
                invitee__email=mediator.user.email
            ).update(
                state=EnterpriseMembers.STATE_ACTIVE,
                invitee=None,
                user=mediator.user
            )

        return super().update(mediator, validated_data)

    def update_practice_jurisdictions(self, mediator, practice_jurisdictions):
        for obj in mediator.practice_jurisdictions.all():
            models.Jurisdiction.objects.filter(id=obj.id).delete()
            mediator.practice_jurisdictions.remove(obj)
        for obj in practice_jurisdictions:
            jurisdiction = models.Jurisdiction.objects.create(**obj)
            mediator.practice_jurisdictions.add(jurisdiction)

    def update_firm_locations(self, mediator, firm_locations):
        for obj in mediator.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            mediator.firm_locations.remove(obj)
        for obj in firm_locations:
            firm_location = models.FirmLocation.objects.create(**obj)
            mediator.firm_locations.add(firm_location)

    def update_education(self, mediator, educations):
        """ Обновите образование адвоката, используя данные из сериализатора. """
        for obj in mediator.education.all():
            models.MediatorEducation.objects.filter(id=obj.id).delete()
        models.MediatorEducation.objects.bulk_create(
            models.MediatorEducation(mediator=mediator, **education_data)
            for education_data in educations
        )

    def update_registration_attachments(
        self, mediator, registration_attachments
    ):
        """ Обновите registration_attachments, используя данные из сериализатора. """
        current_attachments = mediator.registration_attachments.all()

        # Идентификаторы, полученные из запросов
        input_files_urls = set(registration_attachments)

        # Идентификаторы вложений адвоката
        existing_files_urls = set(current_attachments.values_list(
            'attachment', flat=True
        ))

        to_add = input_files_urls - existing_files_urls
        to_delete = existing_files_urls - input_files_urls

        current_attachments.filter(attachment__in=to_delete).delete()

        models.MediatorRegistrationAttachment.objects.bulk_create(
            models.MediatorRegistrationAttachment(
                mediator=mediator,
                attachment=file_url,
            )
            for file_url in to_add
        )


class MediatorOnboardingSerializer(MediatorSerializer):
    """OnboardingSerializer for mediator"""

    def update(self, mediator_id, validated_data):
        mediator = models.Mediator.objects.get(pk=mediator_id)
        user = mediator.user
        user.onboarding = True
        user.save()
        fee_types = validated_data.pop('fee_types', None)
        education = validated_data.pop('education', None)
        practice_jurisdictions = validated_data.pop(
            'practice_jurisdictions', []
        )
        firm_locations = validated_data.pop(
            'firm_locations', []
        )
        registration_attachments = validated_data.pop(
            'registration_attachments', []
        )
        payment_type = validated_data.pop('payment_type', None)
        appointment_type = validated_data.pop(
            'appointment_type', None
        )
        spoken_language = validated_data.pop(
            'spoken_language', None
        )

        if fee_types is not None:
            mediator.fee_types.set(fee_types)
        if payment_type is not None:
            mediator.payment_type.set(payment_type)
        if appointment_type is not None:
            mediator.appointment_type.set(appointment_type)
        if spoken_language is not None:
            mediator.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in mediator.practice_jurisdictions.all():
                models.Jurisdiction.objects.filter(id=obj.id).delete()
                mediator.practice_jurisdictions.remove(obj)
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(
                    **obj
                )
                mediator.practice_jurisdictions.add(jurisdiction)

        # Создать профиль местоположения фирмы
        for obj in mediator.firm_locations.all():
            models.FirmLocation.objects.filter(id=obj.id).delete()
            mediator.firm_locations.remove(obj)
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            mediator.firm_locations.add(location)

        # Создание записей об образовании адвоката
        if education is not None:
            for obj in mediator.education.all():
                models.MediatorEducation.objects.filter(id=obj.id).delete()
            models.MediatorEducation.objects.bulk_create(
                models.MediatorEducation(mediator=mediator, **education_data)
                for education_data in education
            )
        # Добавление вложений
        models.MediatorRegistrationAttachment.objects.bulk_create(
            models.MediatorRegistrationAttachment(
                mediator=mediator, attachment=file_url
            )
            for file_url in registration_attachments
        )

        return super().update(mediator, validated_data)


class MediatorRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, MediatorSerializer
):
    """ Зарегистрироватьсериализатор для адвоката. """
    payment_method = serializers.CharField(required=False)
    avatar = serializers.CharField(source='user.avatar', required=False)
    plan = serializers.SlugRelatedField(
        queryset=PlanProxy.objects.filter(active=True),
        slug_field='id',
        required=False
    )
    education = MediatorEducationSerializer(
        many=True, allow_empty=False, required=False)

    specialities = serializers.ManyRelatedField(
        source='user.specialities',
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=models.Speciality.objects.all()
        ),
        required=False
    )

    class Meta(MediatorSerializer.Meta):
        fields = MediatorSerializer.Meta.fields + (
            'password1',
            'password2',
            'payment_method',
            'plan'
        )
        relations = MediatorSerializer.Meta.relations + (
            'email',
            'avatar',
            'first_name',
            'last_name'
        )
        extra_kwargs = {
            'fee_rate': {
                'required': False
            },
            'fee_types': {
                'required': False
            },
            'avatar': {
                'required': False
            },
            'license_info': {
                'required': False
            },
            'years_of_experience': {
                'required': False
            },
            'appointment_type': {
                'required': False
            },
            'payment_type': {
                'required': False
            },
            'spoken_language': {
                'required': False
            }
        }

    def validate(self, data):
        """ Проверьте регистрационные данные. """
        invite_uuid = self.context.get('invite_uuid', None)
        if invite_uuid:
            invite = models.Invite.objects.get(pk=invite_uuid)
            if invite.user:
                raise ValidationError(
                    'User is already registered with that invite')
            #if invite.user_type != 'mediator':
            #    raise ValidationError(
            #        "You can't register as mediator with '{}' invite".format(
            #            invite.user_type
            #        ))

        data = super().validate(data)
        return super(MediatorSerializer, self).validate(data)

    def create_related(self, user):
        """ Сохраните запись об адвокате.
        Сначала мы создаем запись об адвокате, затем связываем связанные модели.
        """
        # Извлеките данные, которые будут установлены после создания доверенности
        mediator_data = self.validated_data.copy()
        fee_types = mediator_data.pop('fee_types', None)
        education = mediator_data.pop('education', None)
        practice_jurisdictions = mediator_data.pop(
            'practice_jurisdictions', []
        )
        firm_locations = mediator_data.pop(
            'firm_locations', []
        )
        registration_attachments = mediator_data.pop(
            'registration_attachments', []
        )
        # Удалить поля, связанные с платежной информацией
        mediator_data.pop('payment_method', None)
        payment_type = mediator_data.pop('payment_type', None)
        plan = mediator_data.pop('plan', None)
        appointment_type = mediator_data.pop(
            'appointment_type', None
        )
        spoken_language = mediator_data.pop(
            'spoken_language', None
        )
        mediator_data['user'] = user

        # Поля M2M необходимо задать после создания доверенности
        mediator = models.Mediator.objects.create(**mediator_data)

        # Хранить платежные данные
        FinanceProfile.objects.create(
            user=mediator.user,
            initial_plan=plan,
        )
        if fee_types is not None:
            mediator.fee_types.set(fee_types)
        if payment_type is not None:
            mediator.payment_type.set(payment_type)
        if appointment_type is not None:
            mediator.appointment_type.set(appointment_type)
        if spoken_language is not None:
            mediator.spoken_language.set(spoken_language)
        if practice_jurisdictions is not None:
            for obj in practice_jurisdictions:
                jurisdiction = models.Jurisdiction.objects.create(**obj)
                mediator.practice_jurisdictions.add(jurisdiction)

        # Создать профиль местоположения фирмы
        for obj in firm_locations:
            location = models.FirmLocation.objects.create(**obj)
            mediator.firm_locations.add(location)

        # Создание записей об образовании адвоката
        if education is not None:
            models.MediatorEducation.objects.bulk_create(
                models.MediatorEducation(mediator=mediator, **education_data)
                for education_data in education
            )
        # Добавление вложений
        models.MediatorRegistrationAttachment.objects.bulk_create(
            models.MediatorRegistrationAttachment(
                mediator=mediator, attachment=file_url
            )
            for file_url in registration_attachments
        )

        #  Добавить пользователя в список отраслевых контактов приглашающего
        invite_uuid = self.context.get('invite_uuid')
        if invite_uuid: 
            invite = models.Invite.objects.get(pk=invite_uuid)
            if invite.user_type == models.Invite.USER_TYPE_MEDIATOR:
                from apps.business.models import Lead

                user_to_invite = models.AppUser.objects.get(pk=invite.user_id)
                Lead.objects.create(
                    client=invite.inviter.client,
                    mediator=user_to_invite.mediator,
                    enterprise_id=None
                )
                
            else:
                invite.inviter.mediator.industry_contacts.add(user)
            invite.user = user
            invite.save()


class MediatorRegisterValidateSerializer(serializers.Serializer):
    """ Сериализатор для проверки процесса регистрации адвоката """
    stage = serializers.ChoiceField(choices=['first', 'second'], required=True)


class MediatorRegisterValidateFirstStepSerializer(
    AppUserRelatedRegisterSerializerMixin
):
    """ Простой сериализатор для проверки первого шага регистрации адвоката. """
    username = serializers.ReadOnlyField()


class MediatorRegisterValidateSecondStepSerializer(
    MediatorSerializer
):
    """ Простой сериализатор для проверки шага 2d-регистрации адвоката. """
    email = serializers.ReadOnlyField(source='user.email')

    def prepare_instance(self, attrs):
        """ Переопределен метод, чтобы заставить работать метод `instance.clean_user()`.
        Поскольку этот сериализатор используется для проверки регистрации адвоката
        на 2-м шаге у нас нет экземпляра "user" для текущего адвоката
        (потому что мы проверяем только поля 2d-шага, а "электронная почта` там отсутствует).
        Таким образом, проверка экземпляра `clean_user` прерывается в модели mediator.

        Чтобы исправить это, для пустого экземпляра "App User" установлено значение related
        экземпляр сериализатора.
        """
        instance = super().prepare_instance(attrs)
        instance.user = models.AppUser()
        return instance
