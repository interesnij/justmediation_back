from rest_framework import serializers

from taggit_serializer.serializers import TagListSerializerField

from apps.core.api.serializers import BaseSerializer

from .. import models


class NewsSerializer(BaseSerializer):
    """API serializer for news."""

    # ImageSpecField needs this to work with drf
    #image_thumbnail = serializers.ImageField(read_only=True)
    tags = TagListSerializerField()
    categories = TagListSerializerField()

    class Meta:
        model = models.News
        fields = (
            'id',
            'title',
            'description',
            'image',
            'image_thumbnail',
            'tags',
            'categories',
            'created',
            'modified',
            'author'
        )


class NewsTagSerializer(BaseSerializer):
    """API serializer for news tags."""

    class Meta:
        model = models.NewsTag
        fields = (
            'id',
            'name',
            'slug',
        )


class NewsCategorySerializer(BaseSerializer):
    """API serializer for news categories."""

    class Meta:
        model = models.NewsCategory
        fields = (
            'id',
            'name',
            'slug',
        )
