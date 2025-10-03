from django.utils import timezone
from rest_framework import serializers

__all__ = (
    'LocationSerializer',
    'UploadSerializer',
    'URLSerializer',
    'SuccessErrorUrlRequestSerializer',
)


class URLSerializer(serializers.Serializer):
    """ Простой сериализатор, который возвращает поле `url`. """
    url = serializers.URLField(required=False)


class UploadSerializer(serializers.Serializer):
    """ Сериализатор для загрузки изображений. """
    upload = serializers.ImageField(required=True)


class SuccessErrorUrlRequestSerializer(serializers.Serializer):
    """ Простой сериализатор, который получает поля URL-адресов `success` и `error`. """
    success_url = serializers.URLField(required=True)
    error_url = serializers.URLField(required=True)


class LocationSerializer(serializers.Serializer):
    """ Сериализатор местоположения.
    Для использования с моделью GeoDjango.
    """
    lat = serializers.DecimalField(max_digits=10, decimal_places=6,
                                   required=True)
    lon = serializers.DecimalField(max_digits=10, decimal_places=6,
                                   required=True)

    def to_representation(self, obj):
        """ Преобразуйте слова в формат json. """
        lon, lat = obj.coords
        return {
            'lon': lon,
            'lat': lat
        }

    def to_internal_value(self, data):
        """ Преобразуйте данные в тип python. """
        try:
            self.lon = data['lon']
            self.lat = data['lat']
            return 'POINT({0} {1})'.format(data['lon'], data['lat'])
        except KeyError:
            return super().to_internal_value(data)

    def save(self, user=None):
        """ Обновите экземпляр пользователя действительными данными. """
        if user:
            user.location = self.validated_data
            user.location_updated = timezone.now()
            user.save()
        return user
