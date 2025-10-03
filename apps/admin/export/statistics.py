import arrow
import tablib
from libs.export.resources import ExcelResource
from ..services import get_apps_stats


class AppStatisticsResource(ExcelResource):
    """Ресурс для экспорта статистики приложений в XLS для администратора. """

    def __init__(self):
        """ Ресурс инициализации ."""
        super().__init__(instance=None, extension='xls')
        self.stats_data = get_apps_stats()

    @property
    def filename(self) -> str:
        """ Подготовьте имя файла для экспорта. """
        date_now = arrow.utcnow().strftime('%Y-%m-%d')
        return f'(JustMediation) Dashboard Stats for {date_now}.{self.extension}'

    def export(self) -> bytes:
        """ Экспортируйте данные в виде файла excel. """
        data = tablib.Dataset()

        user_stats = self.stats_data['users_stats']
        data.append(('User app stats', ''))
        self.write_stats_data(data, user_stats)

        business_stats = self.stats_data['business_stats']
        data.append(('Business app stats', ''))
        self.write_stats_data(data, business_stats)

        forums_stats = self.stats_data['forums_stats']
        data.append(('Forums app stats', ''))
        self.write_stats_data(data, forums_stats)
        return self.convert_to_bytes(data)

    def write_stats_data(self, data: tablib.Dataset, stats):
        """ Запишите данные о состоянии в набор данных. """
        for stat in stats:
            data.append(tuple(stat.values()))
        data.append(['']*2)
