from rest_framework import status
from rest_framework.exceptions import APIException


class WrongTransitionException(APIException):
    """ Это исключение должно возникать, когда вы не можете выполнить изменение статуса
    Примеры:
        try:
            obj.activate()
            obj.save()
        except TransitionNotAllowed:
            raise WrongTransitionException
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Action is not allowed for current status'
