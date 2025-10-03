from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ModelSerializer


class FakeAppConfig(AppConfig):
    """ Конфигурация для поддельного приложения.
    Атрибуты:
        app_urls (str): путь к модулю с URL-адресами приложений, например:
            'apps.utils.custom_fields.tests.my_fake_app.urls'
        api_urls (str): путь к модулю с URL-адресами API приложения, например:
            'apps.utils.custom_fields.tests.my_fake_app.api.urls'
    Примеры:
        from libs.apps import FakeAppConfig

        class CustomFieldsFakeAppConfig(FakeAppConfig):
            api_urls = 'apps.utils.custom_fields.tests.' \
                       'custom_fields_fake_app.api.urls'
            name = 'apps.utils.custom_fields.tests.custom_fields_fake_app'
    """

    app_urls = None
    api_urls = None


def is_fake_app(app_config):
    """ Проверьте, связано ли app_config с поддельным приложением.

    Аргументы:
        app_config (AppConfig): экземпляр конфигурации приложения для проверки
    Возвращается:
        bool: True, если приложение является поддельным
    """
    return isinstance(app_config, FakeAppConfig)


class LibsAppConfig(AppConfig):
    """ Настройте для выполнения некоторого кода при загрузке конфигурации приложения. """

    name = 'libs'
    verbose_name = _('Libs')

    def ready(self):
        """ Обновите сопоставления сериализатора Django Rest Framework.
        Сопоставления получаются из `настроек.REST_FRAMEWORK_CUSTOM_FIELD_MAPPING`
        Чтобы это сработало, приложение `библиотеки` должно быть определено после
        `rest_framework`
        """
        # Переопределить cities_light admin
        from libs.django_cities_light import admin  # noqa
        field_mapping_settings = getattr(
            settings,
            'REST_FRAMEWORK_CUSTOM_FIELD_MAPPING',
            {}
        )
        field_mapping = ModelSerializer.serializer_field_mapping
        field_mapping.update(
            {import_string(k): import_string(v) for k, v in
             field_mapping_settings.items()}
        )
