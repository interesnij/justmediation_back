from rest_framework import serializers
from ....core.api.serializers import BaseSerializer
from ....users.api.serializers import (
    AppUserShortSerializer,
    AppUserWithoutTypeSerializer,
)
from ... import models
from .extra import AttachmentSerializer
from .matter import ShortMatterSerializer


class ActivitySerializer(BaseSerializer):
    """ Сериализатор для модели `Activity` """
    matter_data = ShortMatterSerializer(source='matter', read_only=True)
    user_data = AppUserWithoutTypeSerializer(source='user', read_only=True)

    class Meta:
        model = models.Activity
        fields = (
            'id',
            'title',
            'matter',
            'matter_data',
            'user',
            'user_data',
            'type',
            'created',
            'modified',
        )


class ShortActivitySerializer(ActivitySerializer):
    avatar = serializers.FileField(source='user.avatar', read_only=True)

    class Meta(ActivitySerializer.Meta):
        fields = [
            'id',
            'title',
            'avatar',
            'matter',
            'type',
            'created',
            'modified',
        ]


class NoteSerializer(BaseSerializer):
    """ Сериализатор для модели `Note`. """
    matter_data = ShortMatterSerializer(source='matter', read_only=True)
    created_by_data = AppUserShortSerializer(
        source='created_by', read_only=True
    )
    client_data = AppUserShortSerializer(
        source='client', read_only=True
    )
    attachments = serializers.SerializerMethodField()

    attachments_data = AttachmentSerializer(
        source='attachments',
        many=True,
        required=False
    )

    def get_attachments(self, obj):
        """
        Использует AttachmentSerializer для сохранения вложения
        связывает и создает связь с объектом.
        """
        attachments = self.context['request'].data.get('attachments', [])
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            obj.attachments.add(file)
        return obj.attachments.values_list('id', flat=True)

    class Meta:
        model = models.Note
        fields = (
            'id',
            'title',
            'text',
            'matter',
            'matter_data',
            'client',
            'client_data',
            'created_by',
            'created_by_data',
            'created',
            'modified',
            'attachments',
            'attachments_data'
        )
        read_only_fields = (
            'created_by',
        )

    def get_fields(self):
        """ Установите набор запросов matter в значение user matters. """
        fields = super().get_fields()
        user = self.user
        if not user or user.is_anonymous:
            return fields
        if user.is_mediator:
            fields['matter'].queryset = models.Matter.objects.\
                available_for_user(user=user)
        return fields

    def validate(self, attrs):
        """ Установите создателя заметки. """
        attrs['created_by'] = self.user
        return super().validate(attrs)


class UpdateNoteSerializer(NoteSerializer):
    """ Обновите сериализатор для модели `Note`. """

    class Meta(NoteSerializer.Meta):
        read_only_fields = NoteSerializer.Meta.read_only_fields + (
            'matter',
        )

    def create_or_update_attachments(self, attachments):
        attachment_ids = []
        for attachment in attachments:
            attachment_instance, created = models.Attachment.objects.\
                update_or_create(pk=attachment.get('id'), defaults=attachment)
            attachment_ids.append(attachment_instance.pk)
        return attachment_ids

    def update(self, instance, validated_data):
        attachments = validated_data.pop('attachments', [])
        instance.attachments.set(
            self.create_or_update_attachments(attachments))
        return super().update(instance, validated_data)


class VoiceConsentSerializer(BaseSerializer):
    """ Сериализатор для модели `VoiceConsent`. """
    matter_data = ShortMatterSerializer(source='matter', read_only=True)

    class Meta:
        model = models.VoiceConsent
        fields = (
            'id',
            'title',
            'file',
            'matter',
            'matter_data',
        )
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=models.VoiceConsent.objects.all(),
                fields=('title', 'matter'),
                message=(
                    'You are trying to upload a duplicate voice consent. '
                    'Please try again.'
                )
            ),
        )

    def get_fields(self):
        """ Установите набор запросов matter в значение user matters. """
        fields = super().get_fields()
        user = self.user
        if not user or user.is_anonymous:
            return fields
        fields['matter'].queryset = models.Matter.objects.available_for_user(
            user=user
        )
        return fields


class MatterSharedWithSerializer(BaseSerializer):
    """ Сериализатор для модели `MatterSharedWith`. """
    matter_data = ShortMatterSerializer(source='matter', read_only=True)
    user_data = AppUserShortSerializer(source='user', read_only=True)

    class Meta:
        model = models.MatterSharedWith
        fields = (
            'id',
            'user',
            'user_data',
            'matter',
            'matter_data',
        )


class InvoiceActivitySerializer(BaseSerializer):
    """ Сериализатор для модели `InvoiceActivity` """

    class Meta:
        model = models.InvoiceActivity
        fields = (
            'id',
            'activity',
            'created',
            'modified',
        )


class InvoiceLogSerializer(BaseSerializer):
    """ Сериализатор для модели `InvoiceLog` """

    class Meta:
        model = models.InvoiceLog
        fields = (
            'id',
            'status',
            'method',
            'log',
            'created',
            'modified',
        )
