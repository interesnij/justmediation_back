import base64
import json
import os
import re
import uuid
from datetime import datetime
from shutil import make_archive
from tempfile import NamedTemporaryFile, TemporaryDirectory
from time import mktime
from typing import Any, Type
from django.utils.safestring import mark_safe
import pytz
from PIL import Image
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.data import JsonLexer


def get_base_url() -> str:
    """ Получите текущий домен интерфейса. """
    current_site = 'https://app.justmediationhub.com/'

    return current_site


def get_admin_base_url() -> str:
    """ Получите домен администратора. """
    current_site = 'https://backend.justmediationhub.com/admin/'

    return current_site


def get_random_filename(filename):
    """ Получите случайное имя файла.
    Генерирует случайное имя файла, содержащее уникальный идентификатор и
    расширение имени файла, например: `photo.jpg `.

    Если расширение слишком длинное (у нас была проблема с этим), замените его на
    UUID тоже

    Аргументы:
        new_filename (str): Имя файла.
    Возвращается:
        new_filename (str): ``9841422d-c041-45a5-b7b3-467179f4f127.ext``.

    """
    path = str(uuid.uuid4())
    ext = os.path.splitext(filename)[1]
    if len(ext) > 15:
        ext = str(uuid.uuid4())

    return ''.join([path, ext.lower()])


def struct_time_to_timezoned(struct_time):
    """ Преобразуйте объект `struct_time` в часовой пояс `datetime.datetime` .
    Результат предназначен для передачи в django `DateTimeField` с указанием часового пояса
    """
    timestamp = mktime(struct_time)
    utc_date = datetime.utcfromtimestamp(timestamp)
    timezoned = utc_date.replace(tzinfo=pytz.utc)
    return timezoned


def get_file_extension(url):
    """ Извлеките расширение файла из пути/URL.
    Аргументы:
        url (str): Путь к файлу
    Возвращается:
        Строка: расширение файла
    Пример:
        'dir/subdir/file.ext' -> 'ext'
    """
    return os.path.splitext(url)[1][1:]


class NewImage(object):
    """ Контекстный менеджер для создания временного файла изображения.
    Пример:
        with NewImage() as img:
            self.image = img
    """

    def __init__(self, width=500, height=500, ext='PNG', color='green',
                 prefix=None):
        self.width = width
        self.height = height
        self.color = color
        self.ext = ext
        self.prefix = prefix

    def __enter__(self):
        image = Image.new('RGB', (self.width, self.height), self.color)
        self.tmp_file = NamedTemporaryFile(
            delete=False,
            suffix='.{0}'.format(self.ext.lower()),
            prefix=self.prefix,
        )
        image.save(self.tmp_file.name, self.ext)
        return self.tmp_file

    def __exit__(self, *args):
        os.unlink(self.tmp_file.name)


class ZipArchive(object):
    """ Контекстный менеджер для создания временного zip-архива с файлами.
    Структура файлов и каталогов в архиве:
        some_file.doc (if `file_without_folder` is True)
        /some_folder
            some_music_file.mp3
            some_image_file.png
    """

    def __init__(self, file_without_folder=False, file_with_invalid_ext=False):
        self.file_without_folder = file_without_folder
        self.file_with_invalid_ext = file_with_invalid_ext

    def __enter__(self):
        self.tmp_dir = TemporaryDirectory()
        self.tmp_subdir = TemporaryDirectory(dir=self.tmp_dir.name)

        self.tmp_zip = NamedTemporaryFile()
        self.tmp_file = NamedTemporaryFile(
            dir=self.tmp_subdir.name, suffix='.png')
        self.another_tmp_file = NamedTemporaryFile(
            dir=self.tmp_subdir.name, suffix='.mp3')

        # создать файл без папки
        if self.file_without_folder:
            self.tmp_file_without_parent_dir = NamedTemporaryFile(
                dir=self.tmp_dir.name,
                suffix='.mp3'
            )

        if self.file_with_invalid_ext:
            self.tmp_file_with_invalid_ext = NamedTemporaryFile(
                dir=self.tmp_subdir.name,
                suffix='.undefined'
            )

        self.image = Image.new('RGB', (1280, 720), 'green')
        self.image.save(self.tmp_file.name, 'PNG')

        self.zip_file = make_archive(self.tmp_zip.name, 'zip',
                                     self.tmp_dir.name)

        return {
            'tmp_zip': self.tmp_zip,
            'tmp_dir': self.tmp_dir,
            'tmp_file': self.tmp_file,
            'tmp_subdir': self.tmp_subdir,
            'zip_file': self.zip_file,
        }

    def __exit__(self, *args):
        self.tmp_file.close()
        self.another_tmp_file.close()

        if self.file_without_folder:
            self.tmp_file_without_parent_dir.close()

        if self.file_with_invalid_ext:
            self.tmp_file_with_invalid_ext.close()

        self.tmp_subdir.cleanup()
        self.tmp_dir.cleanup()
        return True


def get_object_fullname(obj):
    """ Получите полное имя класса объекта в Python.
    Может использоваться для преобразования класса объекта в строку и последующего 
    использования для его восстановления используя `import_string`.
    ПРЕДУПРЕЖДЕНИЕ: используемая простейшая реализация в некоторых случаях может не сработать
    """
    return '.'.join([obj.__module__ + "." + obj.__class__.__name__])


def bytes_to_base_64(data: bytes) -> str:
    """Shortcut to convert simple `bytes` data to base64."""
    return base64.b64encode(data).decode('ascii')


def get_filename_from_path(path: str) -> str:
    """ Ярлык для извлечения имени файла из `path`. """
    full_filename = os.path.basename(path)
    return full_filename


def json_prettified(json_instance: dict) -> str:
    """ Функция для отображения красивой версии json в html.
    Бесстыдно скопировано с:
    https://www.pydanny.com/pretty-formatting-json-django-admin.html

    """

    # Преобразуйте данные в отсортированный JSON с отступом
    response = json.dumps(json_instance, sort_keys=True, indent=2)

    # Усеките данные. Изменяйте по мере необходимости
    response = response[:5000]

    # Получите средство форматирования пигментов
    formatter = HtmlFormatter(style='colorful')

    # Выделите данные
    response = highlight(response, JsonLexer(), formatter)

    # Получите таблицу стилей
    style = "<style>" + formatter.get_style_defs() + "</style><br>"

    # Обезопасьте вывод
    return mark_safe(style + response)


def get_lookup_value(instance: Any, lookup: str) -> Type:
    """ Получите экземпляр, связанный со значением `lookup`.

    Usage:
        > get_lookup_value(<Invoice instance>, 'matter.mediator')
        > <Mediator instance>
    """
    attrs = lookup.split('.')
    value = instance
    for attr in attrs:
        value = getattr(value, attr)
    return value


def get_datetime_from_str(date: str, format: str = '%Y-%m-%d') -> datetime:
    """ Подготовьте объект datetime из str в желаемом формате. """
    return datetime.strptime(date, format)


def invalidate_cached_property(instance: Any, property_name: str):
    """ Сделать недействительным значение кэшированного свойства. """
    try:
        del instance.__dict__[property_name]
    except KeyError:
        pass


def get_latest_version(changelog_filepath: str) -> str:
    "1"


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True
