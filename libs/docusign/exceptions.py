from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException

__all__ = (
    'GetJWTTokenException',
    'GetAccessTokenException',
    'GetUserDataException',
    'CreateEnvelopeException',
    'UpdateEnvelopeException',
    'CreateEditEnvelopeViewException',
    'UserHasNoConsentException',
    'NoEnvelopeExistsException',
)


class GetJWTTokenException(APIException):
    """ Пользовательское исключение для отслеживания ошибок с помощью олицетворения. """
    default_detail = _("Couldn't impersonate user in DocuSign")


class GetAccessTokenException(APIException):
    """ Пользовательское исключение для отслеживания ошибок при получении токена доступа. """
    default_detail = _("Couldn't get access token for user from DocuSign")


class GetUserDataException(APIException):
    """ Пользовательское исключение для отслеживания ошибок при получении пользовательских данных. """
    default_detail = _("Couldn't get user data from DocuSign")


class CreateEnvelopeException(APIException):
    """ Пользовательское исключение для отслеживания ошибок при создании конверта. """
    default_detail = _("Couldn't create Envelope in DocuSign")


class UpdateEnvelopeException(APIException):
    """ Пользовательское исключение для отслеживания ошибок при обновлении конверта. """
    default_detail = _("Couldn't update Envelope in DocuSign")


class CreateEditEnvelopeViewException(APIException):
    """ Пользовательское исключение для отслеживания ошибок при создании 
    вида редактирования конверта. """
    default_detail = _("Couldn't create edit view for Envelope in DocuSign")


class NoEnvelopeExistsException(APIException):
    """ Пользовательское исключение для отслеживания ошибок, когда конверт больше не существует. """
    default_detail = _("Envelope doesn't exist in DocuSign")


class UserHasNoConsentException(APIException):
    """ Пользовательское исключение для отслеживания ошибок, когда пользователь не 
    дает согласия. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User has no consent in DocuSign")
