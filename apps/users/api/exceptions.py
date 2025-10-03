from rest_framework import status
from rest_framework.exceptions import APIException


class MediatorSubscriptionError(APIException):
    """Represent errors with creation stripe subscription mediator"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Action is not allowed for current status'
