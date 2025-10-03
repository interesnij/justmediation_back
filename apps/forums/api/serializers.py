from django.db import IntegrityError

from rest_framework import serializers

from apps.core.api.serializers import BaseSerializer
from apps.forums.models import (
    Comment,
    FollowedPost,
    ForumPracticeAreas,
    Post,
    Topic,
)
from apps.users.api.serializers import (
    AppUserShortSerializer,
    AppUserWithoutTypeSerializer,
    SpecialitySerializer,
)


class CommentSerializer(BaseSerializer):
    """Serializer for `post` model."""

    SINGLE_POST_ACTIONS = ('retrieve', 'create', 'update', 'partial_update')

    author = AppUserWithoutTypeSerializer(
        read_only=True,
    )
    current_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
        source='author',
    )
    user_type = serializers.CharField(
        read_only=True,
        source='author.user_type',
    )
    position = serializers.IntegerField(
        default=0, read_only=True
    )

    class Meta:
        model = Comment
        fields = (
            'id',
            'post',
            'author',
            'text',
            'current_user',
            'created',
            'modified',
            'user_type',
            'position',
        )
        read_only_fields = (
            'created',
            'modified',
            'position',
            'author',
        )

    def validate_post(self, post):
        """Check post consistency.

        Restrict user to change comments post.

        """
        if not self.instance:
            return post
        if post != self.instance.post:
            raise serializers.ValidationError(
                "You can not change comment's post"
            )
        return post


class PostCommentSerializer(BaseSerializer):
    class Meta:
        model = Post
        fields = (
            'id',
            'title',
        )


class CommentTopicSerializer(BaseSerializer):
    author = AppUserWithoutTypeSerializer()
    post = PostCommentSerializer()

    class Meta:
        model = Comment
        fields = (
            'author',
            'post',
            'author',
            'text',
            'created',
            'modified',
        )


class TopicSerializer(BaseSerializer):
    """Serializer for `Topic` model."""

    last_post = CommentTopicSerializer(read_only=True)
    practice_area_data = SpecialitySerializer(
        source='practice_area',
        read_only=True
    )
    followed = serializers.SerializerMethodField(read_only=True)

    def get_followed(self, obj):
        return self.context['request'].user in obj.followers.all()

    class Meta:
        model = Topic
        fields = (
            'id',
            'title',
            'icon',
            'description',
            'practice_area',
            'practice_area_data',
            'post_count',
            'comment_count',
            'last_post',
            'created',
            'modified',
            'followers_count',
            'followed'
        )
        read_only_fields = (
            'post_count',
            'post_count',
            'created',
            'modified',
            'followers_count',
            'followed'
        )


class PostSerializer(BaseSerializer):
    """Serializer for `topic` model."""

    last_comment = CommentSerializer(read_only=True)
    message = serializers.CharField(source='description')
    first_comment = CommentSerializer(read_only=True)
    followed = serializers.SerializerMethodField(read_only=True)
    description = serializers.CharField(source='topic.description')
    topic_data = TopicSerializer(source='topic', read_only=True)
    last_comment_time = serializers.SerializerMethodField(read_only=True)
    author = AppUserShortSerializer(read_only=True)

    def get_followed(self, obj):
        return self.context['request'].user in obj.followers.all()

    def get_last_comment_time(self, obj):
        return obj.last_comment.created if obj.last_comment else None

    class Meta:
        model = Post
        fields = (
            'id',
            'topic',
            'title',
            'last_comment',
            'first_comment',
            'comment_count',
            'created',
            'modified',
            'followers_count',
            'followed',
            'description',
            'last_comment_time',
            'topic_data',
            'author',
            'message'
        )
        read_only_fields = (
            'topic',
            'comment_count',
            'created',
            'modified',
            'followers_count',
            'followed',
            'description',
            'last_comment_time',
            'topic_data'
        )


class PostCreateUpdateSerializer(TopicSerializer):
    message = serializers.CharField(source='description')
    current_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Post
        fields = (
            'id',
            'topic',
            'title',
            'message',
            'last_comment',
            'first_comment',
            'comment_count',
            'current_user',
            'author'
        )
        read_only_fields = (
            'last_comment',
            'first_comment',
            'comment_count',
            'created',
            'modified',
        )

    def validate(self, attrs):
        attrs['author'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        """Create topic with first post."""
        validated_data.pop('current_user')
        post = super().create(validated_data)
        post.refresh_from_db()
        return post


class FollowedPostSerializer(BaseSerializer):
    """Serializer class for `FollowedTopic` model."""
    post_data = PostSerializer(
        read_only=True,
        source='post',
    )
    post = serializers.IntegerField(
        write_only=True,
        source='post_id',
    )
    author = serializers.HiddenField(
        write_only=True,
        default=serializers.CurrentUserDefault(),
        source='follower',
    )
    follower = AppUserShortSerializer(
        read_only=True
    )

    class Meta:
        model = FollowedPost
        fields = (
            'id',
            'post',
            'post_data',
            'author',
            'unread_comments_count',
            'last_read_comment',
            'follower'
        )
        read_only_fields = (
            'unread_comment_count',
            'last_read_comment',
        )

    def create(self, validated_data):
        """Handle integrity error on creation.

        This method is overwritten to prevent 500 error from happening, as it
        possible for user to follow same post twice. This will cause
        integrity error.

        """
        try:
            instance = super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                'Impossible to follow this topic'
            )
        return instance


class TopicShortSerializer(BaseSerializer):
    """Short serializer for topics model"""
    class Meta:
        model = Topic
        fields = (
            'id',
            'title',
            'post_count',
        )


class PracticeAreaWithPostedMattersSerializer(BaseSerializer):
    """Serializes Speciality with its posted matters."""
    posts = serializers.SerializerMethodField(read_only=True)
    posts_count = serializers.SerializerMethodField(read_only=True)

    def get_posts_count(self, obj):
        return obj.posted_matter.count()

    def get_posts(self, obj):
        from apps.business.api.serializers.posted_matters import (
            PostedMatterSerializer,
        )
        return PostedMatterSerializer(obj.posted_matter, many=True).data

    class Meta:
        model = ForumPracticeAreas
        fields = (
            'id', 'title', 'posts', 'posts_count'
        )


class PracticeAreaSerializer(BaseSerializer):
    """Serializer for forum practice Areas model."""

    class Meta:
        model = ForumPracticeAreas
        fields = (
            'id', 'title'
        )
