from django.core.exceptions import ValidationError
from rest_framework import serializers
from libs.api.exceptions import ConflictError
from libs.django_cities_light.api.serializers import (
    CitySerializer,
    CountrySerializer,
    RegionSerializer,
)
from apps.core.api.serializers import BaseSerializer
from ....users import models
from ...models import Invite
from .user import AppUserWithoutTypeSerializer


class InviteSerializer(BaseSerializer):
    """Serializer for Invite model."""
    user = AppUserWithoutTypeSerializer(read_only=True)

    # оставьте старое поле "клиент" для обратной совместимости со старыми мобильными телефонами
    client = AppUserWithoutTypeSerializer(read_only=True)
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CitySerializer(source='city', read_only=True)

    class Meta:
        model = models.Invite
        fields = (
            'uuid',
            'user',
            'client',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'address',
            'country',
            'country_data',
            'state',
            'state_data',
            'city',
            'city_data',
            'zip_code',
            'role',
            'note',
            'client_type',
            'organization_name',
            'message',
            'sent',
            'user_type',
        )
        read_only_fields = (
            'uuid',
            'user',
            'client',
            'sent',
        )

    def validate_email(self, email):
        """ Проверьте, зарегистрирован ли пользователь уже.
        Если пользователь уже зарегистрирован, вызовите ConflictError(409).
        """
        instance = self.get_instance()
        instance.email = email
        if Invite.objects.filter(email=email, inviter=self.user).count() > 0:
            raise ValidationError('You already invited that user')
        try:
            instance.clean_email()
        except ValidationError as error:
            raise ConflictError(
                detail={
                    'id': error.params['user_pk'],
                    'user_type': error.params['user_type'],
                    'detail': error.message,
                }
            )
        return email

    def save(self, **kwargs):
        """Set `inviter` field to current user"""
        if not self.instance:
            self.validated_data['inviter'] = self.user
        return super().save(**kwargs)


class UpdateInviteSerializer(InviteSerializer):
    job = serializers.CharField(source='role')

    class Meta(InviteSerializer.Meta):
        fields = InviteSerializer.Meta.fields + (
            'job',
        )
        read_only_fields = (
            'email',
        )

    def validate(self, attrs):
        invite = self.get_instance()
        if isinstance(invite, models.Invite) \
                and invite.client_type == 'client' \
                and attrs['client_type'] == 'lead':
            raise ValidationError('Can not be lead')
        return super().validate(attrs)
