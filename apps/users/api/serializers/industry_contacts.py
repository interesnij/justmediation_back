
from django.contrib.auth import get_user_model
from rest_framework import serializers
from ....promotion.api.serializers import EventShortSerializer
from ...models import Invite
from .mediator_links import MediatorEducationSerializer
from .extra import (
    FeeKindSerializer,
    FirmLocationSerializer,
    JurisdictionsSerializer,
    LanguageSerializer,
    PaymentTypeSerializer,
    SpecialitySerializer,
)

class IndustryContactSerializer(serializers.Serializer):
    """ Упорядочивает отраслевые контакты адвоката. """
    user_id = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(source='full_name')
    firm = serializers.SerializerMethodField(read_only=True)
    type = serializers.CharField(source='user_type', read_only=True)
    phone = serializers.SerializerMethodField(read_only=True)
    pending = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(read_only=True)
    avatar = serializers.FileField(read_only=True)

    def get_firm(self, obj):
        try:
            if isinstance(obj, Invite):
                return
            obj_type = getattr(obj, obj.user_type, None)
            return obj_type.firm_name if obj_type else None
        except Exception:
            return None

    def get_phone(self, obj):
        if isinstance(obj, Invite):
            return obj.phone
        obj_type = getattr(obj, obj.user_type, None)
        return obj_type.user.phone if obj_type else None

    def get_pending(self, obj):
        if isinstance(obj, Invite):
            return True
        return False

    def get_user_id(self, obj):
        if isinstance(obj, Invite):
            return obj.uuid
        elif isinstance(obj, get_user_model()):
            return obj.id
        else:
            return obj.user_id

    class Meta:
        fields = (
            'user_id',
            'name',
            'firm',
            'type',
            'phone',
            'email',
            'pending',
            'avatar'
        )


class PersonalDetailSerializer(IndustryContactSerializer):
    """ Сериализует личные данные контактного лица из адвокатской отрасли """
    practice_areas = SpecialitySerializer(
        source='specialities',
        many=True
    )
    languages = serializers.SerializerMethodField(read_only=True)

    def get_languages(self, obj):
        languages_query_set = obj.mediator.spoken_language.all()

        return LanguageSerializer(
            languages_query_set,
            many=True
        ).data

    class Meta:
        fields = (
            'id',
            'name',
            'firm',
            'type',
            'type',
            'phone',
            'email',
            'years_of_experience',
            'practice_areas',
            'languages',
        )


class IndustryContactAboutSerializer(IndustryContactSerializer):
    """ Сериализует информацию о контактном лице адвокатской отрасли. """
    jurisdictions = serializers.SerializerMethodField(
        read_only=True
    )
    education = serializers.SerializerMethodField(
        read_only=True
    )
    biography = serializers.SerializerMethodField(read_only=True)

    def get_biography(self, obj):
        return getattr(
            getattr(
                obj,
                'mediator',
                None
            )
        ).biography

    def get_jurisdictions(self, obj):
        if obj.user_type == 'mediator':
            jurisdictions_qs = obj.mediator.practice_jurisdictions.all()
        return JurisdictionsSerializer(
            jurisdictions_qs,
            many=True
        ).data

    def get_education(self, obj):
        if obj.user_type == 'mediator':
            return MediatorEducationSerializer(
                obj.mediator.education,
                many=True
            ).data

    class Meta:
        fields = (
            'biography',
            'jurisdictions_and_registrations',
            'education'
        )

class IndustryContactDetails(serializers.Serializer):
    personal_details = serializers.SerializerMethodField(read_only=True)
    about = serializers.SerializerMethodField(read_only=True)
    payment_methods = serializers.SerializerMethodField(read_only=True)
    fee_types = serializers.SerializerMethodField(read_only=True)
    firm_locations = serializers.SerializerMethodField(read_only=True)
    address = serializers.SerializerMethodField(read_only=True)

    def get_address(self, obj):
        """Return user's address"""
        user_obj = getattr(
            obj,
            'mediator',
            None
        )
        if user_obj:
            return [obj.address for obj in user_obj.firm_locations.all()]
        else:
            return None

    def get_firm_locations(self, obj):
        return FirmLocationSerializer(
            getattr(
                obj,
                'mediator',
            ).firm_locations.all(),
            many=True
        ).data

    def get_personal_details(self, obj):
        return PersonalDetailSerializer(obj).data

    def get_about(self, obj):
        return IndustryContactAboutSerializer(obj).data

    def get_payment_methods(self, obj):
        return PaymentTypeSerializer(
            getattr(
                obj,
                'mediator',
            ).payment_type.all(),
            many=True
        ).data

    def get_fee_types(self, obj):
        return FeeKindSerializer(
            getattr(
                obj,
                'mediator',
            ).fee_types.all(),
            many=True
        ).data

    class Meta:
        fields = (
            'personal_details',
            'about',
            'fee_types',
            'payment_methods',
            'firm_locations',
        )

class IndustryContactMediatorDetails(IndustryContactDetails):
    """ Сериализует данные адвоката для контактов в отрасли. """

    events = EventShortSerializer(read_only=True, many=True)

    class Meta:
        fields = (
            'personal_details',
            'about',
            'events',
            'fee_types',
            'payment_methods',
            'firm_locations'
        )
