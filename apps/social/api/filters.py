from django_filters import rest_framework as filters

from .. import models


class ChatFilter(filters.FilterSet):
    """Filter for Chat model."""
    type = filters.CharFilter(method='filter_type')

    class Meta:
        model = models.Chats
        fields = {
            'id': ['exact', 'in'],
            'participants': ['exact', ],
            'is_favorite': ['exact'],
            'is_group': ['exact']
        }

    def filter_type(self, queryset, name, value):
        """Filter matter which is shared with me"""
        user = self.request.user
        if user.is_client:
            return queryset
        if value:
            clients = set(user.mediator.matters.values_list(
                'client__user__id', flat=True
            )) | set(
                user.mediator.leads.filter(status='converted').values_list(
                    'client__user__id', flat=True
                )
            )
            chat_types = value.split('|')
            participants = set()
            if 'leads' in chat_types:
                participants |= set(
                    user.mediator.leads.exclude(
                        client__user__in=clients
                    ).values_list(
                        'client__user', flat=True
                    )
                )
            if 'opportunities' in chat_types:
                participants |= set(
                    user.mediator.opportunities.values_list(
                        'client__user', flat=True
                    )
                )
            if 'clients' in chat_types:
                participants |= set(
                    clients
                )
            if 'network' in chat_types:
                participants |= set(
                    user.mediator.industry_contacts.all()
                )
            return queryset.filter(participants__in=participants)
        else:
            return queryset


class MediatorPostFilter(filters.FilterSet):
    """Filter for MediatorPost model."""

    class Meta:
        model = models.MediatorPost
        fields = {
            'id': ['exact', 'in'],
            'author': ['exact', 'in'],
        }
