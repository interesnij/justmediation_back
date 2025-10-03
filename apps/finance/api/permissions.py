from rest_framework import permissions
from ..models import Payment


class IsMediatorHasNoConnectedAccount(permissions.BasePermission):
    """ Разрешение, которое проверяет, что у пользователя еще нет "connected" учетной записи."""

    def has_permission(self, request, view):
        """ Убедитесь, что у пользователя еще нет "connected" учетной записи для прямых депозитов.
        """
        user = request.user
        if not hasattr(user, 'finance_profile'):
            return False
        return user.finance_profile.deposit_account is None


class IsPaymentPayerPermission(permissions.BasePermission):
    """ Разрешение, которое проверяет, что пользователь начал оплату запроса. """

    def has_object_permission(self, request, view, obj: Payment):
        """
        Возвращает `True`, если пользователь является плательщиком.
        """
        return obj.payer_id == request.user.pk
