from django_filters import rest_framework as filters

from .. import models


class NewsFilter(filters.FilterSet):
    """Filter for News model."""

    categories = filters.BaseInFilter(method='filter_categories')
    tags = filters.BaseInFilter(method='filter_tags')

    class Meta:
        model = models.News
        fields = {
            'id': ['exact', 'in'],
            'title': ['istartswith', 'icontains'],
            'description': ['istartswith', 'icontains'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }

    def filter_tags(self, queryset, name, value: list):
        """Filter news by tags."""
        if value:
            return queryset.filler_by_tags(value)
        return queryset

    def filter_categories(self, queryset, name, value: list):
        """Filter news by categories."""
        if value:
            return queryset.filler_by_categories(value)
        return queryset
