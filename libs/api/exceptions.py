import json
from django.core.exceptions import PermissionDenied as CorePermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler
import inflection
from libs import utils


class CustomAPIException(APIException):
    """ Пользовательское исключение для API.
    Позволяет реализовывать пользовательские сообщения об ошибках API. Класс Exception должен быть
    унаследован от класса `Custom API Exception` и может переопределять некоторые из его
    аргументов: status_code, code и message.

    Если атрибут status_code не переопределен - ему присваивается значение 500.
    Если атрибут code не переопределен - он генерируется из имени класса.
    Если атрибут message не переопределен - для него устанавливается значение message по умолчанию.

    Аргументы:
        code (str): код ошибки.
        message (str): сообщение об ошибке.

    Пример:
        class CustomCodeError(CustomAPIException):
            status_code = 404
            code = 'ABC123'
            message = 'This is custom error message.'

    """
    code = None
    message = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.code:
            self.default_code = self.code
        else:
            self.default_code = inflection.underscore(self.__class__.__name__)

        self.detail = _(self.message or self.detail)
        self.default_detail = self.detail


def custom_exception_handler_simple(exc, context):
    """ Обрабатывайте простые исключения drf.

    Этот пользовательский обработчик исключений для django REST framework обертывает
    ValidationErrors в поле "данные" и добавляет поле `подробности` с
    первая ошибка или сообщение, не относящиеся к полю:
        К сожалению, существуют некоторые проблемы с данными, которые вы передали
    """
    if isinstance(exc, exceptions.ValidationError):
        if 'non_field_errors' in exc.detail:
            exc.detail = {
                'data': exc.detail,
                'detail': exc.detail['non_field_errors'][0]
            }
        else:
            detail = list(exc.detail.values())[0][0]
            exc.detail = {
                'data': exc.detail,
                'detail': detail
            }
    elif isinstance(exc, Http404):
        pass
    elif isinstance(exc, APIException):
        pass
    else:
        detail = str(exc)
        if utils.is_json(detail) and json.loads(detail).get('message'):
            detail = json.loads(detail).get('message')

        exc = ValidationError(detail={
            'detail': detail
        })

    return exception_handler(exc, context)


def custom_exception_handler(exc, context=None):
    """ Обрабатывать исключения для django REST framework.
    Обработчик переносит ошибки проверки в поле `validation_errors` (для поля
    ошибки) и добавляет поля `detail` и `code`.

    Для ошибок, не связанных с полем, отображается сообщение "detail".:
        "К сожалению, есть некоторые проблемы с данными, которые вы передали"

    Аргументы:
        exc (Исключение): экземпляр `исключения` (например, ошибка проверки)
        контекст (dict): контекст исключения

    Возвращать:
        Ответ: ответ на исключение

    Пример:
        # Ошибки, не связанные с полем:
        {
          "detail": "Unable to log in with provided credentials.",
          "code": "validation_errors"
        }

        # Field errors:
        {
          "code": "validation_error",
          "validation_errors": [{
              "errors": ["This password is too common.",],
              "field": "password1"
            }],
          "detail": "Unfortunately, there are some problems with the data
          you committed"
        }

    """
    validation_errors = []

    if isinstance(exc, CorePermissionDenied):
        exc = PermissionDenied()

    if isinstance(exc, Http404):
        exc = NotFound()

    if isinstance(exc, ValidationError):
        code = 'validation_error'
        detail = _(
            'Unfortunately, there are some problems '
            'with the data you committed'
        )

        if 'non_field_errors' in exc.detail:
            detail = exc.detail['non_field_errors'][0]
            exc.detail.pop('non_field_errors')

        if isinstance(exc.detail, list):
            detail = exc.detail[0]

        if isinstance(exc.detail, dict):
            for field, errors in exc.detail.items():
                validation_errors.append({
                    'field': field,
                    'errors': errors
                })
    elif isinstance(exc, APIException):
        code = exc.default_code
        detail = exc.detail
    else:
        # Unhandled Exceptions (e.g. AssertionError)
        return None
    # Исключения, унаследованные уже от `Пользовательского исключения API`
    # иметь надлежащий формат раздела сведений.

    exc.detail = {
        'detail': detail,
        'code': code,
    }

    if validation_errors:
        exc.detail.update({
            'validation_errors': validation_errors
        })

    return exception_handler(exc, context)


class ConflictError(APIException):
    """ Используется для возврата ответа 409 при ошибках. """
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Input conflicts with existing data.')
    default_code = 'conflict'
