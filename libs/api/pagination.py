from collections import OrderedDict
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

__all__ = ('PageLimitOffsetPagination')


class PageLimitOffsetPagination(LimitOffsetPagination):
    page_count = 0

    def paginate_queryset(self, queryset, request, view=None):
        page_queryset = super().paginate_queryset(
            queryset, request, view
        )
        self.page_count = len(page_queryset)
        return page_queryset

    def get_paginated_response(self, data, **kwargs):
        return Response(OrderedDict([
            ('count', self.count),
            ('page_count', self.page_count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]))
