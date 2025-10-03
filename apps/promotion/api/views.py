from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_condition import And, Or

from apps.core.api.views import CRUDViewSet
from apps.users.api.permissions import (
    IsMediatorHasActiveSubscription,
    IsEnterpriseAdmin,
)

from ...promotion import models
from . import filters, permissions, serializers


class EventViewSet(CRUDViewSet):
    """CRUD api viewset for Event model."""
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    filterset_class = filters.EventFilter
    event_permissions = [
        And(
            IsAuthenticated(),
            Or(
                IsMediatorHasActiveSubscription(),
                IsEnterpriseAdmin(),
            )
        )
    ]
    permissions_map = {
        'list': (AllowAny,),
        'retrieve': (AllowAny,),
        'create': event_permissions,
        'update': event_permissions + [permissions.IsEventOrganizer],
        'partial_update': event_permissions + [permissions.IsEventOrganizer],
        'destroy': event_permissions + [permissions.IsEventOrganizer],
    }
    search_fields = (
        'title',
        '@mediator__user__first_name',
        '@mediator__user__last_name',
        'mediator__user__email',
    )
    ordering_fields = (
        'id',
        'start',
        'end',
    )
