import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import yaml


def get_current_swagger_spec_version():
    """ Верните текущую версию спецификации swagger.

    "Текущая версия спецификации swagger" - это та, с которой API считается
    совместимым. Эта функция должна использоваться для сообщения о версии
    в настоящее время поддерживается API.

    Эта реализация получает версию из файла спецификации swagger, на который
    ссылается параметр ACTUAL_SWAGGER_SPEC_FILE.

    Возвращается:
        str: версия спецификации swagger (например, 0.0.42)
    Повышения:
        Неправильно сконфигурировано: если ФАКТИЧЕСКИЙ_SWAGGER_SPEC_FILE не может быть проанализирован
    """
    file_path = settings.ACTUAL_SWAGGER_SPEC_FILE

    try:
        return extract_swagger_spec_version_from_yaml_file(file_path)
    except ValueError as e:
        raise ImproperlyConfigured(
            'Cannot extract version from({0}): {1}'.format(file_path, e)
        ) from e


def extract_swagger_spec_version_from_yaml_file(file_path):
    """ Проанализируйте данный файл swagger, чтобы получить его версию.
    Аргументы:
        file_path (str): Путь к локальному файлу спецификации
    Возвращается:
        String: версия файла swagger (например, 0.0.42)
    Повышения:
        ValueError: если указанный `file_path` недоступен или каким-либо образом недействителен
    """
    try:
        if os.path.exists(file_path):
            with open(file_path) as f:
                raw_spec = f.read()
        else:
            raise ValueError(
                'Unknown scheme or such local file does not exist'
            )
        spec = yaml.safe_load(raw_spec)
        return spec['info']['version']
    except Exception as e:
        raise ValueError('{0}'.format(e)) from e
