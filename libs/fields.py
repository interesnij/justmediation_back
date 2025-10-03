import typing
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import gettext_lazy as _


class URLTemplateValidator(validators.URLValidator):
    """ Валидатор, который проверяет, является ли шаблон URL допустимым или нет.
    Использование:
        Например, вам нужно сохранить шаблон URL, который имеет параметры
        like id и начинается и выглядит следующим образом:
            https://example.com/stuff?id ={id}&starts={запуски}
        Тогда все, что вам нужно сделать, это передать список ключей шаблонов в __init__.
        Вот так: Средство проверки шаблона URL('id', 'starts')

    """

    def __init__(self, *keys, **kwargs):
        """ Запустите валидатор и установите контекст шаблона. """
        super().__init__(**kwargs)
        self.context = {key: None for key in keys}

    def __call__(self, value):
        """ Убедитесь, что в шаблоне есть необходимый контекст. """
        super().__call__(value)

        # Убедитесь, что в шаблоне есть все необходимые ключи
        for key in self.context.keys():
            if f'{key}' not in value:
                raise ValidationError(_('Incorrect template'))

        # Убедитесь, что форматирование работает должным образом
        try:
            value.format(**self.context)
        except (KeyError, IndexError):
            raise ValidationError(_('Incorrect template'))


class URLTemplateField(fields.URLField):
    """ Поле URL, которое принимает шаблоны URL. """

    def __init__(self, keys: typing.Sequence[str], **kwargs):
        """ Установите ключи для валидатора шаблона URL validator. """
        self.default_validators = [URLTemplateValidator(*keys)]
        super().__init__(**kwargs)
