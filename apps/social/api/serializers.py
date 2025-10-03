import rest_framework.exceptions
from rest_framework import serializers
from ...core.api.serializers import BaseSerializer
from ...users.api.serializers import (
    AppUserWithoutTypeSerializer,
    MediatorShortSerializer,
    ParticipantsSerializer,
)
from ...users.models import AppUser
from .. import models, services
from ..signals import new_chat_message


class UpdateChatSerializer(BaseSerializer):
    """Serializer for Chat model."""
    participants_data = ParticipantsSerializer(
        source='participants', many=True, read_only=True
    )
    participants = serializers.ManyRelatedField(
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=AppUser.objects.all()
        ))
    is_favorite = serializers.BooleanField(
        required=False
    )
    is_group = serializers.BooleanField(required=False)

    def validate(self, attrs):
        participants = set(attrs.get('participants', []))
        participants |= set(self.instance.participants.all())
        participants.add(self.context['request'].user)
        participant_types = [
            p.user_type for p in participants
        ]
        if participant_types.count('client') > 1:
            raise rest_framework.exceptions.APIException(
                'A group chat can only have 1 client type participant'
            )
        if len(participants) < 2:
            raise rest_framework.exceptions.APIException(
                'At least one participant other than '
                'creator is required to create the chat.'
            )
        attrs['is_group'] = len(participants) > 2
        return super().validate(attrs)

    class Meta:
        model = models.Chats
        fields = (
            'id',
            'title',
            'chat_channel',
            'participants',
            'participants_data',
            'is_favorite',
            'is_archived',
            'is_group',
        )
        relations = (
            'participants',
        )
        read_only_fields = (
            'chat_channel',
        )

    def update(self, instance, validated_data):
        participants = set(validated_data.pop('participants', []))
        chat = super().update(instance, validated_data)
        if participants:
            services.add_participants_to_single_group_chat(
                chat=chat,
                participants=participants,
                inviter=self.context['request'].user
            )
        chat.single_chat_participants.filter(
            appuser=self.context['request'].user
        ).update(is_favorite=validated_data.get('is_favorite', False))
        return chat


class ChatSerializer(BaseSerializer):
    """Serializer for Chat model."""
    participants_data = ParticipantsSerializer(
        source='participants', many=True, read_only=True
    )
    participants = serializers.ManyRelatedField(
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=AppUser.objects.all()
        ))
    is_favorite = serializers.SerializerMethodField(
        read_only=True,
        required=False
    )
    is_group = serializers.BooleanField(required=False)
    chat_type = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(
        read_only=True
    )

    def validate(self, attrs):
        participants = attrs.get('participants', [])
        participant_types = [p.user_type for p in participants]
        if participant_types.count('client') > 1:
            raise rest_framework.exceptions.APIException(
                'A group chat can only have 1 client type participant'
            )
        if self.context['request'].user not in participants:
            participants.append(self.context['request'].user)
        if len(participants) < 2:
            raise rest_framework.exceptions.APIException(
                'At least one participant other than '
                'creator is required to create the chat.'
            )
        attrs['participants'] = participants
        attrs['is_group'] = len(participants) > 2
        return super().validate(attrs)

    def get_last_message(self, obj):
        return MessageShortSerializer(
            obj.messages.order_by('-created').first()
        ).data

    def get_chat_type(self, instance):
        user = self.context['request'].user
        if self.context['request'].user.is_mediator:
            obj = user.mediator
        else:
            return None
        participants = list(instance.participants.exclude(
            id=self.context['request'].user.id
        ).values_list('id', flat=True))

        if user.user_type == 'mediator':
            clients = list(
                obj.matters.values_list('client__user__id', flat=True)
            ) + list(
                obj.leads.filter(status='converted').values_list(
                    'client__user__id', flat=True
                )
            )
        else:
            clients = list(
                obj.leads.filter(status='converted').values_list(
                    'client__user__id', flat=True
                )
            )
        if any([p in clients for p in participants]):
            return 'clients'

        opportunities = list(
            obj.opportunities.values_list(
                'client__user__id', flat=True
            )
        )
        if any([p in opportunities for p in participants]):
            return 'opportunities'

        leads = list(
            obj.leads.filter(status='active').values_list(
                'client__user__id', flat=True
            )
        )
        if any([p in leads for p in participants]):
            return 'leads'

        return 'network'

    def get_is_favorite(self, obj):
        chat = models.SingleChatParticipants.objects.filter(
            appuser=self.context['request'].user,
            chat=obj
        ).first()
        return chat.is_favorite if chat else False

    class Meta:
        model = models.Chats
        fields = (
            'id',
            'title',
            'chat_channel',
            'participants',
            'participants_data',
            'last_message',
            'is_favorite',
            'is_archived',
            'is_group',
            'chat_type',
            'created'
        )
        relations = (
            'participants',
        )
        read_only_fields = (
            'chat_channel',
        )

    def create(self, validated_data):
        """Create group chat and add participants."""
        participants = set(validated_data.pop('participants', []))
        chat = super().create(validated_data)
        services.add_participants_to_single_group_chat(
            chat=chat,
            participants=participants,
            inviter=self.context['request'].user
        )
        return chat


class ChatOverviewSerializer(ChatSerializer):
    last_message = serializers.SerializerMethodField(
        read_only=True
    )
    client_data = serializers.SerializerMethodField(
        read_only=True
    )

    def get_last_message(self, obj):
        return MessageShortSerializer(
            obj.messages.order_by('-created').first()
        ).data

    def get_client_data(self, obj):
        clients = obj.participants.exclude(
            id=self.context['request'].user.id
        )
        return AppUserWithoutTypeSerializer(
            clients,
            many=True
        ).data

    class Meta(ChatSerializer.Meta):
        fields = (
            'id',
            'title',
            'client_data',
            'chat_channel',
            'last_message',
            'is_favorite',
            'is_archived',
            'is_group',
            'chat_type',
            'created'
        )


class MediatorPostSerializer(BaseSerializer):
    """Serializer for MediatorPost model."""
    author_data = MediatorShortSerializer(
        source='author', read_only=True
    )
    # ImageSpecField needs this to work with drf
    image_thumbnail = serializers.ImageField(read_only=True)

    class Meta:
        model = models.MediatorPost
        fields = (
            'id',
            'author',
            'author_data',
            'title',
            'image',
            'image_thumbnail',
            'body',
            'body_preview',
            'created',
            'modified',
        )
        read_only_fields = (
            'author',
            'author_data',
            'image_thumbnail',
            'created',
            'modified',
        )

    def validate(self, attrs):
        """Set author."""
        attrs = super().validate(attrs)
        attrs['author_id'] = self.user.pk
        return attrs


class ContactShareSerializer(serializers.Serializer):
    """Validated input data for contact sharing"""
    is_pending = serializers.BooleanField()
    shared_with = serializers.ManyRelatedField(
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=AppUser.objects.all()
        ))


class MessageAttachmentSerializer(BaseSerializer):
    """serializer for message attachments"""
    size = serializers.SerializerMethodField(read_only=True)
    title = serializers.SerializerMethodField(read_only=True)
    #if not title:
    #    title = file.split("/")[-1]
    
    def get_title(self, obj):
        if not obj.title:
            obj.title = obj.file.split("/")[-1]
        print("title", obj.title)
        print("file", obj.file)

    def get_size(self, obj):
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

    class Meta:
        model = models.MessageAttachment
        fields = (
            'message',
            'title',
            'size',
            'file'
        )


class MessageSerializer(BaseSerializer):
    """Serializer for chat messages."""
    author_data = AppUserWithoutTypeSerializer(
        source='author',
        read_only=True
    )
    files = MessageAttachmentSerializer(
        source='attachment',
        many=True,
        read_only=True,
    )

    class Meta:
        model = models.Message
        fields = (
            'id',
            'author',
            'author_data',
            'type',
            'chat',
            'text',
            'files',
            'timestamp1',
            'created',
        )

    def validate(self, attrs):
        attrs['author'] = self.user
        return super().validate(attrs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        new_chat_message.send(
            instance=instance,
            inviter=self.user,
            sender=models.Message
        )
        return instance


class MessageShortSerializer(MessageSerializer):
    """Serializer for chat messages."""

    class Meta(MessageSerializer.Meta):
        fields = (
            'id',
            'chat',
            'text',
            'type',
            'files',
            'timestamp1',
            'created',
        )
