from rest_framework import mixins
from rest_framework.permissions import AllowAny
from ....core.api.views import BaseViewSet
from .. import filters, serializers
from ...models import MediatorUniversity


class MediatorUniversityViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """ Просмотр Api для получения списка всех университетов адвокатов. """
    serializer_class = serializers.MediatorUniversitySerializer
    base_permission_classes = (AllowAny,)
    queryset = MediatorUniversity.objects.verified_universities()
    filter_class = filters.MediatorUniversityFilter
    search_fields = [
        'title',
    ]
