from rest_framework.permissions import AllowAny

from apps.core.api.views import ReadOnlyViewSet

from .. import models
from . import filters, serializers


class NewsViewSet(ReadOnlyViewSet):
    """Viewset for `News` model.

    Read only API methods.

    """
    queryset = models.News.objects.all().prefetch_related(
        'tags', 'categories'
    )
    serializer_class = serializers.NewsSerializer
    filterset_class = filters.NewsFilter
    ordering_fields = (
        'title',
        'created',
        'modified',
        'author'
    )
    search_fields = ('title',)
    base_permission_classes = (AllowAny,)
    lookup_value_regex = '[0-9]+'


class BaseTaggitViewSet(ReadOnlyViewSet):
    """Base view set for taggit base models."""
    ordering_fields = (
        'name',
        'created',
        'modified'
    )
    search_fields = ('name',)
    base_permission_classes = (AllowAny,)


class NewsTagViewSet(BaseTaggitViewSet):
    """Viewset for `NewsTag` model.

    Read only API methods.

    """
    queryset = models.NewsTag.objects.all()
    serializer_class = serializers.NewsTagSerializer


class NewsCategoryViewSet(BaseTaggitViewSet):
    """Viewset for `NewsCategory` model.

    Read only API methods.

    """
    queryset = models.NewsCategory.objects.all()
    serializer_class = serializers.NewsCategorySerializer
