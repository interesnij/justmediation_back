import functools
from django.core.exceptions import ImproperlyConfigured, ValidationError
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django_fsm import TransitionNotAllowed, has_transition_perm
from ..exceptions import TransitionFailedException
from .exceptions import WrongTransitionException


def transition_method(method_name):
    """ Замените оформленный метод методом, который выполняет переход
    объекта из одного состояния в другое.
    
    Аргументы:
        method_name (str): имя метода перехода модели
    Возвращается:
        функция: декоратор
    """

    def method_decorator(method):
        """ Выбрасывает метод и возвращает новый метод для выполнения перехода
        
        Аргументы:
            метод (функция): пустой метод для украшения
        Возвращается:
            функция: метод перехода
        """

        @functools.wraps(method)
        def api_method(self: GenericViewSet, *args, **kwargs):
            """ Способ изменения статуса объекта с помощью django-fsm

            Повышения:
                Неправильное исключение TransitionException: когда переход не разрешен
            Возвращается:
                Ответ: сериализованный объект и статус HTTP 200
            """
            if not self.transition_result_serializer_class:
                raise ImproperlyConfigured(
                    f'Set transition_result_serializer_class in '
                    f'{self.__class__}'
                )
            transition_object = self.get_object()

            transition = getattr(transition_object, method_name)
            # проверьте, есть ли у текущего пользователя разрешения на переход
            try:
                if not has_transition_perm(transition, self.request.user):
                    raise exceptions.PermissionDenied
            except ValidationError as permission_error:
                raise exceptions.ValidationError(permission_error.message_dict)

            # Получить параметры для перехода
            transition_parameters = {'user': self.request.user}
            serializer_class = self.get_serializer_class()
            if serializer_class:
                context = self.get_serializer_context()
                transition_parameters.update(get_transition_parameters(
                    data=self.request.data,
                    serializer_class=serializer_class,
                    context=context,
                ))

            try:
                transition(**transition_parameters)
                transition_object.save()
            except TransitionFailedException:
                # Сохранить состояние on_error
                transition_object.save()
                return Response(
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except TransitionNotAllowed:
                raise WrongTransitionException

            serializer = self.transition_result_serializer_class(
                transition_object, context=self.get_serializer_context()
            )
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return api_method

    return method_decorator


def get_transition_parameters(data: dict, serializer_class, context) -> dict:
    """ Получите параметры перехода из данных запроса. """
    transition_serializer = serializer_class(
        data=data,
        context=context,
    )
    transition_serializer.is_valid(raise_exception=True)
    return transition_serializer.validated_data
