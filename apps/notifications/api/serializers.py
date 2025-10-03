from rest_framework import serializers

from apps.core.api.serializers import BaseSerializer
from apps.users.api.serializers import AppUserWithoutTypeSerializer

from ...notifications import models
from ..services.resources import RESOURCE_MAPPING


class ShortNotificationGroupSerializer(BaseSerializer):
    """Short version of serializer for `NotificationGroup` model."""

    class Meta:
        model = models.NotificationGroup
        fields = (
            'id',
            'title',
        )


class NotificationTypeSerializer(BaseSerializer):
    """Serializer for `NotificationType` model."""
    group = ShortNotificationGroupSerializer()

    class Meta:
        model = models.NotificationType
        fields = (
            'id',
            'title',
            'runtime_tag',
            'recipient_type',
            'description',
            'group',
        )
        read_only_fields = (
            'runtime_tag',
            'group'
        )


class NotificationGroupSerializer(ShortNotificationGroupSerializer):
    """Serializer for `NotificationGroup` model."""

    types = NotificationTypeSerializer(many=True, read_only=True)

    class Meta(ShortNotificationGroupSerializer.Meta):
        fields = ShortNotificationGroupSerializer.Meta.fields + (
            'types',
        )


class NotificationSerializer(BaseSerializer):
    """Serializer for `Notification` model."""
    runtime_tag = serializers.ReadOnlyField(source='type.runtime_tag')
    content = serializers.SerializerMethodField()
    object_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Notification
        fields = (
            'id',
            'title',
            'object_id',
            'content',
            'type',
            'runtime_tag',
        )

    def get_content(self, notification: models.Notification):
        """Render notification content for web."""
        resource = RESOURCE_MAPPING[notification.type.runtime_tag]
        recipient = getattr(self.context.get('request'), 'user')
        return resource.get_web_notification_content(
            notification, recipient=recipient
        )

    def get_object_id(self, notification: models.Notification):
        try:
            if notification.type.runtime_tag == 'new_matter_shared':
                return notification.content_type.model_class().objects.\
                    select_related('matter').get(
                        pk=notification.object_id
                    ).matter.pk
            elif 'proposal' in notification.type.runtime_tag:
                return notification.content_type.model_class().objects.\
                    select_related('post').get(
                        pk=notification.object_id
                    ).post.pk
            elif 'post' in notification.type.runtime_tag and \
                    notification.type.runtime_tag != 'new_post_on_topic':
                return notification.content_type.model_class().objects.\
                    select_related('post').get(
                        pk=notification.object_id
                    ).post.pk
            elif notification.type.runtime_tag == 'new_message':
                return notification.content_type.model_class().objects.\
                    select_related('post__matter').get(
                        pk=notification.object_id
                    ).post.matter.pk
            elif notification.type.runtime_tag == 'new_billing_item':
                return notification.content_type.model_class().objects.\
                    select_related('matter').get(
                        pk=notification.object_id
                    ).matter.pk
            elif notification.type.runtime_tag == 'new_invoice':
                return notification.content_type.model_class().objects.\
                    select_related('matter').get(
                        pk=notification.object_id
                    ).matter.pk
            elif notification.type.runtime_tag == \
                    'document_uploaded_to_matter':
                return notification.content_type.model_class().objects.\
                    select_related('matter').get(
                        pk=notification.object_id
                    ).matter.pk
            elif notification.type.runtime_tag == \
                    'new_chat_message':
                return notification.content_type.model_class().objects.\
                    select_related('chat').get(
                        pk=notification.object_id
                    ).chat.pk
            return notification.object_id
        except Exception:
            return notification.object_id


class NotificationDispatchSerializer(BaseSerializer):
    """Serializer for `NotificationDispatch` model."""
    notification = NotificationSerializer(read_only=True)
    sender_data = AppUserWithoutTypeSerializer(
        source='sender', read_only=True
    )

    class Meta:
        model = models.NotificationDispatch
        fields = (
            'id',
            'notification',
            'sender',
            'sender_data',
            'status',
            'created',
            'modified',
        )
        read_only_fields = (
            'notification',
        )


class NotificationSettingSerializer(BaseSerializer):
    """Serializer for `NotificationSetting` model."""

    push = serializers.BooleanField(source='by_push', required=False)
    email = serializers.BooleanField(source='by_email', required=False)
    chats = serializers.BooleanField(source='by_chats', required=False)
    matters = serializers.BooleanField(source='by_matters', required=False)
    forums = serializers.BooleanField(source='by_forums', required=False)
    contacts = serializers.BooleanField(source='by_contacts', required=False)

    class Meta:
        model = models.NotificationSetting
        fields = (
            'push',
            'email',
            'chats',
            'matters',
            'forums',
            'contacts',
        )
