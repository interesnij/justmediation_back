from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class AuthError(APIException):
    """ Возникает, когда мы не можем пройти аутентификацию в QB. """


class RefreshTokenExpired(AuthError):
    """ Возникает, когда срок действия обновленного токена QB истек. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Refresh token is expired')


class NotAuthorized(AuthError):
    """ Возникает, когда у клиента QB нет параметров авторизации. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Not authenticated in QuickBooks')


class ObjectNotFound(APIException):
    """ Возникает, когда запрошенный "объект" не найден в QB. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object is not found in QuickBooks')


class SaveObjectError(APIException):
    """ Возникает, когда "объект" по некоторым причинам не может быть сохранен в QB. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object can\'t be saved')


class DuplicatedObjectError(APIException):
    """ Возникает, когда "объект" не может быть сохранен в QB из-за дублирования. """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Object is duplicated')
