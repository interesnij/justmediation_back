from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from apps.business import models
from apps.business.api.serializers.extra import AttachmentSerializer
from apps.business.models import Matter
from apps.business.signals import new_message
from apps.users.api.serializers import AppUserWithoutTypeSerializer


class BusinessPrimaryKeyRelateField(serializers.PrimaryKeyRelatedField):
    """ Фильтруйте важные дела в зависимости от разрешений. """
    def get_queryset(self):
        """ Передайте текущего пользователя в фильтр набора запросов. """
        request = self.context.get('request')
        qs = super().get_queryset()
        if not request or not qs.exists():
            return
        user = request.user
        return qs.available_for_user(user)


class MatterCommentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели `MatterComment`. """
    author = AppUserWithoutTypeSerializer(
        read_only=True,
    )
    post = BusinessPrimaryKeyRelateField(
        queryset=models.MatterPost.objects.all(),
    )
    current_author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
        source='author',
    )
    participants = serializers.ManyRelatedField(
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=get_user_model().objects.all()
        ),
        required=False
    )
    participants_data = AppUserWithoutTypeSerializer(
        source='participants', many=True, read_only=True
    )
    attachments_data = AttachmentSerializer(
        source='attachments',
        many=True,
        required=False
    )

    class Meta:
        model = models.MatterComment
        fields = (
            'id',
            'post',
            'author',
            'current_author',
            'text',
            'participants',
            'participants_data',
            'attachments',
            'attachments_data',
            'created',
            'modified',
            'seen',
            'seen_by_client',
        )
        read_only_fields = (
            'author',
            'seen',
            'seen_by_client',
            'attachments',
            'attachments_data',
        )

    def create(self, validated_data):
        """ Запомнить текущего пользователя запроса как `creator`. """

        if self.context['request'].user.is_mediator:
            validated_data['seen'] = True
            validated_data['post'].seen_by_client = False
        elif self.context['request'].user.is_client:
            validated_data['seen_by_client'] = True
            validated_data['post'].seen = False
        comment = super().create(validated_data)
        comment.participants.add(comment.author)
        comment.save()
        new_message.send(sender=models.MatterComment, instance=comment)
        comment.participants.add(self.context['request'].user)
        attachments = self.context['request'].data.get('attachments', [])
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            comment.attachments.add(file)
        return comment

    def update(self, instance, validated_data):
        attachments = self.context['request'].data.get('attachments', [])
        for obj in instance.attachments.all():
            models.Attachment.objects.filter(id=obj.id).delete()
            instance.attachments.remove(obj)
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            instance.attachments.add(file)
        return super().update(instance, validated_data)


class MatterPostSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели `MatterPost`. """

    matter = BusinessPrimaryKeyRelateField(
        queryset=Matter.objects.all(),
    )
    last_comment = MatterCommentSerializer(
        read_only=True,
    )
    participants = serializers.ManyRelatedField(
        child_relation=serializers.PrimaryKeyRelatedField(
            queryset=get_user_model().objects.all()
        ),
        required=True
    )
    participants_data = AppUserWithoutTypeSerializer(
        source='participants', many=True, read_only=True
    )
    attachments_data = AttachmentSerializer(
        source='attachments',
        many=True,
        required=False
    )

    class Meta:
        model = models.MatterPost
        fields = (
            'id',
            'matter',
            'last_comment',
            'comment_count',
            'title',
            'participants',
            'participants_data',
            'attachments',
            'attachments_data',
            'created',
            'modified',
            'seen',
            'seen_by_client',
        )
        read_only_fields = (
            'seen',
            'seen_by_client',
            'comment_count',
            'attachments',
            'attachments_data',
        )

    def create(self, validated_data):
        """ Запомнить текущего пользователя запроса как `creator`. """

        if self.context['request'].user.is_mediator:
            validated_data['seen'] = True
        elif self.context['request'].user.is_client:
            validated_data['seen_by_client'] = True
        post = super().create(validated_data)
        post.participants.add(self.context['request'].user)
        attachments = self.context['request'].data.get('attachments', [])
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            post.attachments.add(file)
        return post

    def update(self, instance, validated_data):
        attachments = self.context['request'].data.get('attachments', [])
        for obj in instance.attachments.all():
            models.Attachment.objects.filter(id=obj.id).delete()
            instance.attachments.remove(obj)
        attachments = [{'file': attachment} for attachment in attachments]
        serializer = AttachmentSerializer(data=attachments, many=True)
        serializer.is_valid(raise_exception=True)
        saved_files = serializer.save()
        for file in saved_files:
            instance.attachments.add(file)
        return super().update(instance, validated_data)

    def validate(self, attrs):
        if len(attrs['participants']) == 0:
            raise ValidationError('Participants should be selected.')
        return super().validate(attrs)
