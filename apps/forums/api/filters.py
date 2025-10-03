from django_filters import rest_framework as filters

from ...forums import models

__all__ = (
    'PostFilter',
    'FollowedPostFilter',
)


class PostFilter(filters.FilterSet):
    """Filter for `Post` model"""
    followed = filters.BooleanFilter(method='filter_followed', )

    class Meta:
        model = models.Post
        fields = {
            'id': ['exact', 'in'],
            'topic': ['exact', 'in'],
            'followed': ['exact'],
            'author': ['exact'],
            'comment_count': ['exact', 'in'],
        }

    def filter_followed(self, queryset, name, value):
        """Filter posts that current user follows.

        If value `true` was passed to filter, we filter queryset to return
        posts that current user follows.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(followers=user)
        return queryset


class TopicFilter(filters.FilterSet):
    """Filter for `Topic` model"""
    followed = filters.BooleanFilter(method='filter_followed', )

    class Meta:
        model = models.Topic
        fields = {
            'id': ['exact', 'in'],
            'practice_area': ['exact', 'in'],
            'followed': ['exact'],
            'featured': ['exact'],
        }

    def filter_followed(self, queryset, name, value):
        """Filter topics that current user follows.

        If value `true` was passed to filter, we filter queryset to return
        topics that current user follows.

        """
        user = self.request.user

        if value and user.is_authenticated:
            queryset = queryset.filter(followers=user)
            print(queryset)
        return queryset


class FollowedPostFilter(filters.FilterSet):
    """Filter for `FollowedTopic` model"""

    class Meta:
        model = models.FollowedPost
        fields = {
            'id': ['exact', 'in'],
            'post': ['exact', 'in'],
        }
