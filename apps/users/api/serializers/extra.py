from rest_framework import serializers
from libs.django_cities_light.api.serializers import (
    CitySerializer,
    CountrySerializer,
    RegionSerializer,
)
from ....core.api.serializers import BaseSerializer
from ....users import models


class SpecialitySerializer(BaseSerializer):
    """Serializer for `Speciality` model."""

    class Meta:
        model = models.Speciality
        fields = (
            'id', 'title', 'created_by'
        )

    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.created_by = self.context['request'].user
        obj.save()
        return obj


class FeeKindSerializer(BaseSerializer):
    """Serializer for `FeeKind` model."""

    class Meta:
        model = models.FeeKind
        fields = (
            'id', 'title'
        )

class LawFirmSerializer(BaseSerializer):
    """Serializer for `LawFirm` model."""

    class Meta:
        model = models.LawFirm
        fields = (
            'id', 'name'
        )

class AppointmentTypeSerializer(BaseSerializer):
    """ Serializer for Appointment type """

    class Meta:
        model = models.AppointmentType
        fields = (
            'id', 'title'
        )


class PaymentTypeSerializer(BaseSerializer):
    """ Serializer for Payment Method """

    class Meta:
        model = models.PaymentType
        fields = (
            'id', 'title'
        )


class LanguageSerializer(BaseSerializer):
    """ Serializer for Language """

    class Meta:
        model = models.Language
        fields = (
            'id', 'title'
        )


class CurrenciesSerializer(BaseSerializer):
    """ Serializer for Currencies """

    class Meta:
        model = models.Currencies
        fields = (
            'id', 'title'
        )


class JurisdictionsSerializer(BaseSerializer):
    """ Serializer for Jurisdiction """

    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = RegionSerializer(source='city', read_only=True)

    class Meta:
        model = models.Jurisdiction
        fields = (
            'id',
            'country',
            'country_data',
            'state',
            'state_data',
            'city',
            'city_data',
            'agency',
            'number',
            'year'
        )
        extra_kwargs = {
            'agency': {
                'required': False
            },
            'number': {
                'required': False
            },
            'year': {
                'required': False
            }
        }


class FirmLocationSerializer(BaseSerializer):
    """ Serializer for FirmLocation """

    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CitySerializer(source='city', read_only=True)
    latitude = serializers.CharField(source='city.latitude', read_only=True)
    longitude = serializers.CharField(source='city.longitude', read_only=True)
    if not longitude:
        longitude = "0.0"
    if not latitude:
        latitude = "0.0"

    class Meta:
        model = models.FirmLocation
        fields = (
            'id',
            'country',
            'country_data',
            'state',
            'state_data',
            'city',
            'city_data',
            'address',
            'zip_code',
            'latitude',
            'longitude',
        )


class FirmSizeSerializer(BaseSerializer):
    """ Serializer for FirmSize """

    class Meta:
        model = models.FirmSize
        fields = (
            'id', 'title'
        )


class TimezoneSerializer(BaseSerializer):
    """ Serializer for Timezone """

    class Meta:
        model = models.TimeZone
        fields = (
            'id', 'title'
        )


class MediatorSearchSerializer(serializers.Serializer):
    first_name = serializers.CharField(source='user.first_name')
    middle_name = serializers.CharField(source='user.middle_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    id = serializers.IntegerField(source='user.id')
    avatar = serializers.FileField(source="user.avatar")
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return type(obj).__name__.lower()
