from django_filters.rest_framework import FilterSet

from ...notifications import models

__all__ = (
    'NotificationDispatchFilter',
    'NotificationGroupFilter',
    'NotificationTypeFilter',
)


class NotificationDispatchFilter(FilterSet):
    """Filter for `NotificationDispatch` model."""

    class Meta:
        model = models.NotificationDispatch
        fields = {
            'notification': ['exact', 'in'],
            'notification__title': ['icontains', 'istartswith', ],
            'notification__type': ['exact', 'in'],
            'status': ['exact', 'in'],
        }


class NotificationTypeFilter(FilterSet):
    """Filter for `NotificationType` model."""

    class Meta:
        model = models.NotificationType
        fields = {
            'title': ['icontains', 'istartswith', ],
            'group': ['exact', 'in', ],
        }


class NotificationGroupFilter(FilterSet):
    """Filter for `NotificationGroup` model."""

    class Meta:
        model = models.NotificationGroup
        fields = {
            'title': ['icontains', 'istartswith', ],
        }
