from rest_framework import serializers

from apps.core.api.serializers import BaseSerializer

from ....users import models
from .auth import AppUserRelatedRegisterSerializerMixin
from .user import AppUserRelatedSerializerMixin


class SupportSerializer(AppUserRelatedSerializerMixin, BaseSerializer):
    """Serializer for Support model."""
    avatar = serializers.CharField(source='user.avatar', required=False)
    class Meta:
        model = models.Support
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'description',
            'verification_status',
            'is_paid',
        )
        read_only_fields = (
            'user',
            'verification_status',
            'is_paid',
        )
        relations = (
            'user',
        )


class UpdateSupportSerializer(SupportSerializer):
    """Update serializer for Support users."""

    first_name = serializers.CharField(
        source='user.first_name', read_only=True
    )
    last_name = serializers.CharField(
        source='user.last_name', read_only=True
    )
    email = serializers.EmailField(
        source='user.email', read_only=True
    )


class SupportRegisterSerializer(
    AppUserRelatedRegisterSerializerMixin, SupportSerializer
):
    """Register serializer for Support users."""
    avatar = serializers.CharField(source='user.avatar', required=False)
    class Meta(SupportSerializer.Meta):
        fields = SupportSerializer.Meta.fields + (
            'password1',
            'password2',
        )
        relations = (
            'user',
            'email',
            'avatar',
            'first_name',
            'last_name'
        )

    def validate(self, data):
        """Check registration data."""
        data = super().validate(data)
        return super(SupportSerializer, self).validate(data)

    def create_related(self, user):
        """Save `support` entry."""
        client_data = self.validated_data.copy()
        client_data['user'] = user
        models.Support.objects.create(**client_data)
