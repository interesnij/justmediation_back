from django_filters import rest_framework as filters

from ...promotion import models


class EventFilter(filters.FilterSet):
    """Filter for `Event` model."""
    upcoming = filters.BooleanFilter(method='filter_upcoming',)

    def filter_upcoming(self, queryset, name, value):
        """Filter upcoming events(events that are going to happen).

        If value `true` was passed to filter, we filter queryset to return
        upcoming events(events that are going to happen).

        """
        if value:
            return queryset.upcoming()
        return queryset

    class Meta:
        model = models.Event
        fields = {
            'id': ['exact', 'in'],
            'upcoming': ['exact'],
            'mediator': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'location': ['icontains', 'istartswith'],
            'start': ['gte', 'lte'],
            'end': ['gte', 'lte'],
            'is_all_day': ['exact'],
        }
