from drf_yasg import openapi
from drf_yasg.inspectors import DjangoRestResponsePagination
from apps.business.api.pagination import BillingItemLimitOffsetPagination


class BillingItemPaginationInspector(DjangoRestResponsePagination):
    """ Инспектор разбивки на страницы для предоставления дополнительных полей в спецификации.
        Этот инспектор добавит поля `total_fees` и `total_time` в
        модель ответа выбранного метода с разбивкой по страницам.
    """
    def get_paginated_response(self, paginator, response_schema):
        """ Обновите paged_schema по умолчанию с полями для выставления счетов за время. """
        paged_schema = \
            super().get_paginated_response(paginator, response_schema)

        if isinstance(paginator, BillingItemLimitOffsetPagination):
            paged_schema.properties.update(
                {
                    'total_fees': openapi.Schema(
                        type=openapi.TYPE_NUMBER,
                        title='Sum of all selected fees (on all pages).',
                    ),
                    'total_time': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        title='Total billed time (on all pages).',
                    ),
                }
            )

        return paged_schema
