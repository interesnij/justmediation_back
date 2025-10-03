from django.contrib.auth import get_user_model
from rest_framework import serializers
from libs.api.serializers.fields import DateTimeFieldWithTZ
from apps.core.api.serializers import BaseSerializer
from apps.forums.models import UserStats
from ....users import models
from .extra import SpecialitySerializer


class UserStatsSerializer(BaseSerializer):
    """Serializer for `user_stats` model."""
    class Meta:
        model = UserStats
        fields = (
            'comment_count',
        )


class AppUserTwoFASerializer(BaseSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'phone',
            'twofa',
        )


class AppUserSerializer(BaseSerializer):
    """Serializer for AppUser model."""
    date_joined = DateTimeFieldWithTZ(read_only=True)
    last_login = DateTimeFieldWithTZ(read_only=True)
    forum_stats = UserStatsSerializer(read_only=True)
    verification_status = serializers.CharField(
        source='mediator.verification_status',
        read_only=True,
    )
    client_type = serializers.CharField(
        source='client.client_type',
        read_only=True,
    )
    organization_name = serializers.CharField(
        source='client.organization_name',
        read_only=True,
    )
    specialities_data = SpecialitySerializer(
        source='specialities', many=True, read_only=True
    )

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'date_joined',
            'last_login',
            'forum_stats',
            'avatar',
            'verification_status',
            'client_type',
            'organization_name',
            #'active_subscription',
            'specialities',
            'specialities_data',
            'created',
            'modified',
            'twofa'
        )
        read_only_fields = (
            'email',
            'location',
            'location_title',
        )
        extra_kwargs = {
            'email': {'required': False},
        }

    def get_fields_to_hide(self, instance: models.AppUser) -> tuple:
        """Hide client's email from other clients."""
        fields_to_hide = super().get_fields_to_hide(instance)
        user = self.user
        if (
            user and user.is_client and instance.is_client
            and user.pk != instance.pk
        ):
            return fields_to_hide + ('email',)
        return fields_to_hide

    def to_representation(self, instance):
        if instance.avatar == '[]' or instance.avatar == '':
            instance.avatar = None
        data = super().to_representation(instance=instance)
        return data


class ParticipantsSerializer(AppUserSerializer):
    """Serializer for Participants"""
    address = serializers.SerializerMethodField(
        read_only=True
    )
    opportunity_id = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )
    lead_id = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )

    def get_opportunity_id(self, obj):
        current_user = self.context['request'].user
        if obj.user_type == 'client' and current_user.user_type == 'mediator':
            opportunity = obj.client.opportunities.filter(
                mediator=current_user.mediator
            )
            if opportunity:
                return opportunity.first().id

    def get_lead_id(self, obj):
        current_user = self.context['request'].user
        if obj.user_type == 'client' and current_user.user_type == 'mediator':
            lead = obj.client.leads.filter(
                mediator=current_user.mediator
            )
            if lead:
                return lead.first().id

    def get_address(self, obj):
        """Return user's address"""
        res = []
        if obj and obj.user_type == 'mediator':
            for loc in obj.mediator.firm_locations.all():
                country = loc.country.name if loc.country else None
                state = loc.state.name if loc.state else None
                city = loc.city.name if loc.city else None
                data = {
                    "country": country,
                    "state": state,
                    "city": city,
                    "address": loc.address,
                    "zip_code": loc.zip_code,
                }
                res.append(data)
            return res
        elif obj and obj.user_type == 'client':
            country = obj.client.country.name if obj.client.country else None
            state = obj.client.state.name if obj.client.state else None
            city = obj.client.city.name if obj.client.city else None
            data = {
                "country": country,
                "state": state,
                "city": city,
                "address1": obj.client.address1,
                "address2": obj.client.address2,
                "zip_code": obj.client.zip_code,
            }
            res.append(data)
        return res

    class Meta(AppUserSerializer.Meta):
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'phone',
            'avatar',
            'address',
            'user_type',
            'opportunity_id',
            'lead_id'
        )


class AppUserShortSerializer(serializers.ModelSerializer):
    """Short serializer for AppUser model."""

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'avatar',
            'user_type',
        )

    def to_representation(self, instance):
        if instance.avatar == '[]' or instance.avatar == '':
            instance.avatar = None
        data = super().to_representation(instance=instance)
        return data


class AppUserOverviewSerializer(serializers.ModelSerializer):
    """Short overview serializer for AppUser model."""

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'avatar',
        )

    def to_representation(self, instance):
        if instance.avatar == '[]' or instance.avatar == '':
            instance.avatar = None
        data = super().to_representation(instance=instance)
        return data


class AppUserWithoutTypeSerializer(AppUserShortSerializer):
    """Short serializer for AppUser model with `user_type`.

    Note: When use this serializer don't forget to add `select_related` for
    corresponding user `support`, `client` and `mediator` fields.

    """

    class Meta(AppUserShortSerializer.Meta):
        fields = (
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'avatar',
        )


class AppUserRelatedSerializerMixin(BaseSerializer):
    """Serializer mixin for `Mediator` and `Client` models.

    This serializer mixin contains common fields and update logic required for
    working with `Mediator` and `Client` models through api.

    """
    id = serializers.IntegerField(source='user_id', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    middle_name = serializers.CharField(
        source='user.middle_name',
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', required=True)
    phone = serializers.CharField(source='user.phone', allow_blank=True)
    avatar = serializers.CharField(source='user.avatar', allow_blank=True)
    specialities = serializers.ManyRelatedField(
        source='user.specialities',
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=models.Speciality.objects.all()
        ),
        allow_empty=False
    )
    specialities_data = SpecialitySerializer(
        source='user.specialities', many=True, read_only=True
    )
    twofa = serializers.CharField(source='user.twofa', read_only=True)

    def update(self, instance, validated_data):
        """ Обновите запись экземпляра, связанную с пользователем приложения.
        Сначала мы обновляем пользовательские данные, а после этого обновляем поля экземпляра.
        """
        user_data = validated_data.pop('user', {})
        instance.user.first_name = user_data.pop(
            'first_name', instance.user.first_name
        )
        instance.user.middle_name = user_data.pop(
            'middle_name', instance.user.middle_name
        )
        instance.user.last_name = user_data.pop(
            'last_name', instance.user.last_name
        )
        instance.user.twofa = user_data.pop(
            'twofa', instance.user.twofa
        )
        instance.user.phone = user_data.pop(
            'phone', instance.user.phone
        )
        instance.user.avatar = user_data.pop(
            'avatar', instance.user.avatar
        )
        instance.user.timezone = user_data.pop(
            'timezone', instance.user.timezone
        )
        instance.user.specialities.set(
            user_data.pop(
                'specialities',
                instance.user.specialities.all()
            )
        )
        instance.user.save()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        if instance.user.avatar == '[]' or instance.user.avatar == '':
            instance.user.avatar = None
        data = super().to_representation(instance=instance)
        return data


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField()


class TwoFASerializer(serializers.Serializer):
    twofa = serializers.BooleanField()
