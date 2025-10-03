from datetime import timedelta
from django.db import models
from django.http.response import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
import pdfkit
import tablib


class BaseResource:
    """ Используется для определения общей логики экспорта данных в файл. """
    extension = None
    mimetype = None

    def __init__(self, instance: models.Model, ) -> None:
        """Init resource."""
        self.instance = instance

    @property
    def options(self) -> dict:
        """ Получите различные параметры для файла. """
        return {}

    @property
    def filename(self) -> str:
        """ Получите имя файла экспорта. """
        now = timezone.now().strftime('%Y-%m-%d')
        model = self.instance._meta.model_name.capitalize()
        return f'{model}_{now}.{self.extension}'

    @property
    def content_disposition(self):
        return f'attachment;filename="{self.filename}"'

    @property
    def content_type(self):
        return f'{self.mimetype}; charset=utf-8'

    def get_export_file_response(self, data: bytes) -> HttpResponse:
        """ Ярлык для получения HTTP-ответа с экспортированным файлом
        Метод подготавливает Http-ответ с экспортированным файлом. Этот ответ
        запускает загрузку файла в браузере.
        """
        response = HttpResponse(data, content_type=self.mimetype)
        response['Content-Disposition'] = self.content_disposition
        response['Content-Type'] = self.content_type
        return response


class PDFResource(BaseResource):
    """ Базовый класс для всех ресурсов, связанных с PDF, который определяет рабочий процесс 
    экспорта.

    Этот класс сам обрабатывает экспорт в PDF и представляет для
    него общий интерфейс.
    """

    template = None
    mimetype = 'application/pdf'
    extension = 'pdf'

    def __init__(
        self, instance: models.Model, template: str = None, *args, **kwargs
    ) -> None:
        """ Заставьте пользователя установить свойство `template`. """
        super().__init__(instance=instance)
        assert self.template, '`template` should be defined for PDF resource'
        self.instance = instance
        self.template = template or self.template

    def get_template_context(self) -> dict:
        """ Получите все, что требуется для контекста данных шаблона. """
        return {'object': self.instance}

    @property
    def options(self) -> dict:
        """ Способ получения различных параметров PDF. """
        return {
            'page-size': 'Letter',
            'encoding': 'UTF-8',
        }

    def export(self) -> bytes:
        """ Сделайте экспорт ресурсов в формате PDF.
        Этот метод просто выполняет экспорт соответствующего экземпляра в формате
        определяется "шаблоном".
        Возвращается:
            (байты) PDF в виде строки в байтах
        """
        template = get_template(template_name=self.template)
        context = self.get_template_context()
        html = template.render(context)
        pdf = pdfkit.from_string(html, output_path=False, options=self.options)
        return pdf


class ExcelResource(BaseResource):
    """ Базовый класс для ресурсов, связанных с Excel, который определяет рабочий процесс 
    экспорта. Этот класс обрабатывает экспорт во все поддерживаемые excel 
    форматы и представляет общий интерфейс для этого.
    """
    extension = None
    mimetype = None
    mimetype_map = {
        'xls': 'application/vnd.ms-excel',
        'xlsx': (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        'csv': 'text/csv'
    }

    def __init__(
        self, instance: models.Model, extension: str
    ) -> None:
        """ Заставьте пользователя установить свойство `template`. """
        super().__init__(instance)
        self.instance = instance
        self.extension = extension
        self.mimetype = self.mimetype_map[extension]

    def convert_to_bytes(self, data: tablib.Dataset) -> bytes:
        """ Преобразование данных tabllib в байты с выбранным форматом (расширением) """
        return data.export(self.extension)

    def format_timedelta(self, time: timedelta):
        """ Преобразование данных tabllib в байты с выбранным форматом (расширением) """
        if not time:
            return '00:00:00'
        hours, remaining = divmod(time.seconds, 3600)
        hours += 24 * time.days
        minutes, seconds = divmod(remaining, 60)
        return '{hours}:{minutes:02d}:{seconds:02d}'.format(
            hours=hours, minutes=minutes, seconds=seconds
        )
