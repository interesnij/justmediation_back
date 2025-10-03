from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException

__all__ = (
    'SaveUserConsentException',
)


class SaveUserConsentException(APIException):
    """Custom exception to track errors when user can't save consent."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Can't save user esign consent")
