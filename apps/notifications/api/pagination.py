from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class NotificationLimitOffsetPagination(LimitOffsetPagination):
    """Pagination to add notification info to the pagination data.

    Provide additional info for unread notification, it could be
    accessed easily within single request from frontend. Other wise we should
    add

    """
    def __init__(self):
        self.unread_count = 0

    def paginate_queryset(self, queryset, request, view=None):
        """Collect unread notification from initial queryset.

        This is the only place to access initial queryset inside pagination.

        """
        self.unread_count = queryset.get_unread_count()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data, **kwargs):
        """Provide custom response with unread notification info."""
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('unread_count', self.unread_count),
        ]))
