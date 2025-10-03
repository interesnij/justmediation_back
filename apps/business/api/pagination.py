from collections import OrderedDict
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class BillingItemLimitOffsetPagination(LimitOffsetPagination):
    """ Разбивка на страницы для добавления информации о платежном элементе к данным разбивки 
    на страницы. Предоставьте дополнительную информацию для выбранных данных элемента 
    выставления счетов, чтобы к ним можно было легко получить доступ в рамках одного 
    запроса из интерфейса. В противном случае мы должны добавлять
    """
    def __init__(self):
        self.total_fees = 0
        self.total_time = ''

    def paginate_queryset(self, queryset, request, view=None):
        """ Соберите общую сумму сборов и общее время, затраченное на первоначальный набор запросов.
        Это единственное место для доступа к исходному набору запросов внутри разбивки на страницы.
        """
        self.total_fees = queryset.get_total_fee()
        self.total_time = queryset.get_total_time()
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data, **kwargs):
        """ Предоставьте пользовательский ответ с информацией о времени выставления счета. """
        return Response(OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('total_fees', self.total_fees),
            ('total_time', self.total_time),
        ]))
