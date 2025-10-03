from rest_framework import serializers


class UnknownFieldsValidationMixin(object):
    """ Смешивание для проверки неизвестных полей. """

    def validate(self, attrs):
        """ Проверьте неизвестные поля.
        Вызывает исключение в случае, если отправлено "неизвестно"
        поля в теле запроса в формате json.

        :параметры:
            допустимые поля
        :возвращение:
            возвращает или вызывает исключение Validationexception
        """
        has_unknown_fields = set(self.initial_data.keys()) - set(attrs.keys())

        if has_unknown_fields:
            raise serializers.ValidationError(
                "Unknown fields submitted: " + str(has_unknown_fields))

        return super().validate(attrs)
