from typing import Union
from rest_framework import permissions
from ..models import BillingItem, Invoice

__all__ = (
    'CanEditOrDeleteInvoiceOrBillingItem',
)


class CanEditOrDeleteInvoiceOrBillingItem(permissions.BasePermission):
    """ Проверьте, можно ли отредактировать или удалить счет-фактуру или выставление 
    счета по времени. """

    def has_object_permission(
        self, request, view, obj: Union[Invoice, BillingItem]
    ) -> bool:
        """ Запретить операцию, если объект недоступен для редактирования. """
        return obj.available_for_editing
