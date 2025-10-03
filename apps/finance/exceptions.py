from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class PaymentProfileCreationError(Exception):
    """ Возникает при сбое создания платежных данных """
    def __init__(self, message) -> None:
        self.message = message


class DefinitionPlanTypeError(APIException):
    """ Возникает, когда план подписки не имеет value """
    default_detail = _("Unknown subscription plan type")


class InvalidSubscriptionAction(APIException):
    """ Возникает при попытке изменить неактивную подписку """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("You cannot change an inactive subscription")


class SubscriptionCreationError(APIException):
    """ Возникает, когда у пользователя есть неверные данные для создания подписки """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Failed to create subscription.")
