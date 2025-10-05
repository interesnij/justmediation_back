from datetime import datetime
from typing import Union
from django.db.models import Sum
import tablib
from libs.export.resources import ExcelResource
from ...users.models import AppUser
from .. import models


class MediatorPeriodBusinessResource(ExcelResource):
    """ Ресурс для экспорта бизнес-статистики за период в Excel для адвоката. """

    def __init__(
        self,
        instance: AppUser,
        extension: str,
        period_start: datetime,
        period_end: datetime
    ):
        """Init resource."""
        super().__init__(instance, extension)
        self.instance: AppUser = self.instance
        self.period_start = period_start
        self.period_end = period_end

    @property
    def filename(self) -> str:
        """Prepare filename for export."""
        return (
            f'(justmediationhub) Business report for '
            f'{self.period_start} - {self.period_end}'
            f'.{self.extension}'
        )

    def export(self) -> Union[bytes, str]:
        """ Экспортируйте данные в виде файла excel.
        Сначала мы создаем dataset и устанавливаем две первые строки, в одной отображается 
        информация о периоде, а во второй - заголовки таблиц. После этого мы используем
        метод fill_matters_stats для заполнения набора данных всеми необходимыми 
        статистическими данными.
        """
        data = tablib.Dataset()
        data.append(
            ('Period', f'{self.period_start} - {self.period_end}', '', '')
        )
        data.append(('Client', 'Matter', 'Logged time', 'Earned',))
        self.fill_matters_stats(data=data)
        return self.convert_to_bytes(data)

    def fill_matters_stats(self, data: tablib.Dataset):
        """ Заполните набор данных бизнес-статистикой. """
        matters = models.Matter.objects.with_time_billings(
            user=self.instance,
            period_start=self.period_start,
            period_end=self.period_end,
        ).filter(
            time_spent__isnull=False
        ).order_by('client').prefetch_related('client')
        client_id = None
        for matter in matters:
            # Мы добавляем имя клиента только один раз
            client_name = '' if client_id == matter.client_id \
                else matter.client.full_name
            client_id = matter.client_id
            mediator_time_spent = self.format_timedelta(
                matter.mediator_time_spent
            )
            mediator_fees = matter.mediator_fees or '0.0'
            data.append((
                client_name,
                matter.title,
                mediator_time_spent,
                mediator_fees
            ))
        # Рассчитайте общую сумму сборов и time_spent и добавьте ее в набор данных
        total = matters.aggregate(
            total_mediator_time=Sum('mediator_time_spent'),
            total_mediator_fees=Sum('mediator_fees')
        )
        total_mediator_time = self.format_timedelta(
            total['total_mediator_time']
        )
        total_mediator_fees = total['total_mediator_fees'] or '0.0'
        data.append(('', 'Total', total_mediator_time, total_mediator_fees))
