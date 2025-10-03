from collections import OrderedDict
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework import serializers


class DateTimeFieldWithTimeZone(serializers.DateTimeField):
    """ Поле DateTimeField, в котором сохраняется входной часовой пояс.
    Поле DateTimeField drf по умолчанию преобразует введенное время в часовой пояс UTC (проверьте
    enforce_time zone), это поле проверяет, есть ли у datetime часовой пояс или нет. Если у него
    есть часовой пояс, он возвращает его без изменений, в противном случае он использует значение 
    по умолчанию метод enforce_timezone.
    """

    def enforce_timezone(self, value):
        """ Если значение не имеет часового пояса, принудительно примените его. """
        if timezone.is_aware(value):
            return value
        return super().enforce_timezone(value)


class DateTimeFieldWithTZ(serializers.DateTimeField):
    """ Поля даты и времени с поддержкой tz. """

    def enforce_timezone(self, value):
        """ Укажите tz для полей даты и времени.
        Если `self.default_timezone` равно `None`, всегда возвращайте наивные datetimes.
        Если `self.default_timezone` не равен `None`, верните aware datetimes.
        """
        try:
            tz = timezone._active.value
            if (self.timezone is not None) \
                    and not timezone.is_aware(value):
                return timezone.make_aware(value, tz)
            return value
        except AttributeError:
            return super().enforce_timezone(value)

    def to_representation(self, value):
        """ Возвращает отформатированную дату и время как местное время. """
        value = timezone.localtime(value)
        return super().to_representation(value)


class CustomLocationField(serializers.Serializer):
    """ Поле местоположения для представления точек с 2 координатами.

    django.contrib.gis.geos.Point represented using dict:
    {
        "longitude": 12,
        "latitude": 12
    }
    """

    longitude = serializers.FloatField(
        max_value=180,
        min_value=-180,
        required=True
    )
    latitude = serializers.FloatField(
        max_value=90,
        min_value=-90,
        required=True
    )

    def to_internal_value(self, value: dict) -> Point:
        """ Преобразуйте `dict` в `Point`.
        Аргументы:
            значение (dict): Значение для преобразования

        Возвращается:
            Точка: точка с `x=значением['долгота']` и
            `y=значением['широта']`

        Повышения:
            Ошибка проверки: когда значение не указано, а широта и долгота
                значения, не входящие в соответствующие диапазоны
        """
        value = super().to_internal_value(value)
        return Point(value['longitude'], value['latitude'])

    def to_representation(self, obj: Point) -> OrderedDict:
        """ Преобразуйте из `Point` в `OrderedDict`.

        Аргументы:
            obj (Point): Точка для представления
        Возвращается:
            OrderedDict: Ordereddict с ключами `долгота` и `широта`
                и значения с плавающей точкой
        """
        return OrderedDict([
            ('longitude', obj.x),
            ('latitude', obj.y),
        ])
