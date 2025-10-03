from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ....business import models
from ....core.api.serializers import BaseSerializer
from ....users.api.serializers import (
    AppUserShortSerializer,
    MediatorShortSerializer,
)
from ....users.models import AppUser


class AttachmentSerializer(BaseSerializer):
    """ Сериализатор для модели `Attachment`. """

    file_size = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    def get_file_size(self, obj):
        #x = obj.file.size
        #y = 512000
        #if x < y:
        #    value = round(x/1000, 2)
        #    ext = 'KB'
        #elif x < y*1000:
        #    value = round(x/1000000, 2)
        #    ext = 'MB'
        #else:
        #    value = round(x/1000000000, 2)
        #    ext = 'GB'
        return str(10)+'KB'
        #return str(value)+ext

    def get_file_name(self, obj):
        #return ''
        return obj.file.split('/')[-1]

    class Meta:
        model = models.Attachment
        fields = (
            'file',
            'file_size',
            'file_name',
            'mime_type'
        )
        read_only_fields = (
            'file_size',
            'file_name',
            'mime_type',
        )


class StageSerializer(BaseSerializer):
    """ Сериализатор для модели `Stage` """

    class Meta:
        model = models.Stage
        fields = (
            'id',
            'title',
        )

    @property
    def validated_data(self):
        """ Установите владельца stage. """
        validated_data = super().validated_data
        validated_data['mediator'] = self.user.mediator
        return validated_data


class ChecklistEntrySerializer(BaseSerializer):
    """Сериализатор для модели `ChecklistEntry` """

    class Meta:
        model = models.ChecklistEntry
        fields = (
            'id',
            'description',
        )

    def validate(self, attrs):
        """ Установите владельца записи контрольного списка. """
        attrs['mediator'] = self.user.mediator
        return super().validate(attrs)


class VideoCallSerializer(BaseSerializer):
    """ Сериализатор для модели `VideoCall` """
    participants_data = AppUserShortSerializer(
        source='participants', read_only=True, many=True
    )

    class Meta:
        model = models.VideoCall
        fields = (
            'id',
            'call_url',
            'participants',
            'participants_data'
        )
        relations = (
            'participants',
        )
        read_only_fields = (
            'call_url',
            'created_by',
        )

    def validate_participants(self, participants):
        """ Ограничьте количество участников видеозвонка. """
        if len(participants) > models.VideoCall.MAX_PARTICIPANTS_COUNT:
            raise ValidationError(
                f'You can only invite '
                f'{models.VideoCall.MAX_PARTICIPANTS_COUNT} people'
            )
        return participants

    def get_fields(self):
        """ Ограничить набор запросов участников. """
        fields = super().get_fields()
        user = self.user
        if not user or user.is_anonymous:
            return fields

        had_business_with = AppUser.objects.had_business_with(user=user)
        had_shared_matters_with = AppUser.objects.filter(
            Q(client__matters__shared_links__user_id=user.pk) |
            Q(mediator__user__shared_matters__client_id=user.pk) |
            Q(support__user__shared_matters__client_id=user.pk)
        )

        fields['participants'].child_relation.queryset = AppUser.objects.filter(  # noqa
            Q(id__in=had_business_with.values('id')) |
            Q(id__in=had_shared_matters_with.values('id'))
        )

        return fields


class ReferralSerializer(BaseSerializer):
    """ Сериализатор для модели `Referral` """
    mediator_data = MediatorShortSerializer(source='mediator', read_only=True)

    class Meta:
        model = models.Referral
        fields = (
            'id',
            'mediator',
            'mediator_data',
            'message',
        )


class PaymentMethodsSerializer(BaseSerializer):
    """ Сериализатор для модели `PaymentMethods`. """

    class Meta:
        model = models.PaymentMethods
        fields = (
            'id',
            'title',
        )
