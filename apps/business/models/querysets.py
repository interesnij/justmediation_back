from datetime import datetime, timedelta
from functools import reduce
from django.db.models import (
    BooleanField,
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    When,
)
from django.db.models.query import QuerySet
from ...finance.models.payments.querysets import AbstractPaidObjectQuerySet
from ...users import models as user_models

__all__ = (
    'UserRelatedQuerySet',
    'MatterRelatedQuerySet',
    'LeadQuerySet',
    'MatterQuerySet',
    'BillingItemQuerySet',
    'InvoiceQuerySet',
    'MatterCommentQuerySet',
    'MatterPostQuerySet',
    'NoteQuerySet',
    'VoiceConsentQuerySet',
    'VideoCallQuerySet',
    'MatterSharedWithQuerySet',
)


class UserRelatedQuerySet(QuerySet):
    """ Класс набора запросов, который обеспечивает фильтрацию `available_for_user`.
    Этот набор запросов обеспечивает фильтрацию по доступности информации, связанной с 
    пользователем объекты. Чтобы использовать эти методы qs, в модели должны быть 
    `адвокат` и `клиент` атрибуты.
    """

    def available_for_user(self, user: user_models.AppUser):
        """ Фильтр доступен для пользовательских объектов.
        Случаи:
            1. Запрос пользователя является адвокатом - фильтруйте только те случаи, 
            когда пользователь является адвокатом.
            2. Запрашивать пользователя как клиента - фильтровать только те случаи, 
            когда пользователь является клиент.
        """
        # Исправлено для спецификации swagger
        # if user.user_type == user_models.AppUser.USER_TYPE_STAFF:
        #     return self
        lookup = 'mediator' if user.is_mediator else 'client'
        try:
            return self.filter(
                Q(**{lookup: user.pk}) |
                Q(**{'referral__mediator': user.pk}) |
                Q(**{'shared_with__in': [user]})
            )
        except Exception:
            try:
                return self.filter(
                    Q(**{lookup: user.pk}) | Q(**{'shared_with__in': [user]})
                )
            except Exception:
                return self.filter(**{lookup: user.pk})


class MatterRelatedQuerySet(QuerySet):
    """ Класс набора запросов, который обеспечивает фильтрацию `available_for_user`.
    Этот набор запросов обеспечивает фильтрацию по доступности информации, связанной с вопросом
    объекты. Таким образом, в зависимости от доступности материала связанные объекты также 
    должны быть доступны или нет.
    """

    def available_for_user(self, user: user_models.AppUser):
        """ Фильтр доступен для экземпляров, связанных с пользовательскими вопросами.
        Случаи:
            1. Запрос "Пользователь является адвокатом" - фильтруйте только случаи, связанные с
            вопросами, в которых пользователь является адвокатом, или случаи, связанные с 
            вопросом совместно с пользователем.
            2. Запрос "Пользователь является клиентом" - фильтруйте только экземпляры, 
            относящиеся к вопросам, в которых пользователь является клиентом.
        """
        from . import Matter
        available_matters = Matter.objects.all().available_for_user(user)
        return self.filter(matter__in=available_matters)


class OpportunityQuerySet(UserRelatedQuerySet):
    """ набор запросов модели Opportunity """
    pass


class LeadQuerySet(UserRelatedQuerySet):
    """ набор запросов модели Lead. """

    def aggregate_count_stats(self):
        """ Получите статистику подсчета лидов (по статусу). """
        from . import Lead
        return self.aggregate(
            active_count=Count('pk', filter=Q(status=Lead.STATUS_ACTIVE)),
            converted_count=Count(
                'pk', filter=Q(status=Lead.STATUS_CONVERTED)
            ),
            total_count=Count('pk', ),
        )


class MatterQuerySet(UserRelatedQuerySet):
    """ набор запросов модели  Matter. """

    def available_for_user(self, user: user_models.AppUser):
        """ Фильтр доступен для пользовательских объектов.
        Случаи:
            1. Запрос адвоката - фильтруйте только те вопросы, которыми поделился пользователь 
            (за исключением вопросов, находящихся в стадии рассмотрения`
            или `черновик` состояний, потому что они не могут быть общими).

            2. Запрос клиента - фильтровать только те случаи, когда 
            пользователь является клиентом.
        """
        from ..models import Matter
        qs = super().available_for_user(user)
        if user.is_staff:
            return qs

        shared_matters = user.shared_matters.exclude(
            status__in=[Matter.STATUS_OPEN]
        )
        return self.filter(
            Q(id__in=qs.values('id')) | Q(id__in=shared_matters)
        )

    def open(self):
        """ Короткий путь для получения значения только "открыто". """
        # импорт здесь из-за циклической зависимости
        from . import Matter
        return self.filter(status=Matter.STATUS_OPEN)

    def hourly_rated(self):
        """ Короткий путь для получения только `почасовой` оценки имеет значение. """
        # импорт здесь из-за циклической зависимости
        from . import Matter
        return self.filter(rate_type=Matter.RATE_TYPE_HOURLY)

    def with_invoices_num(self):
        """ Пометьте каждый вопрос количеством счетов-фактур. """
        return self.annotate(num_invoices=Count('invoices'))

    def with_totals(self):
        """Прокомментируйте каждый вопрос с указанием общего количества оплаченного времени, 
        "fees` и `hours`.

        Эта аннотация необходима для повышения производительности получения итоговых данных:
            - `time_billed` (общее затраченное время)
            - `fees_earned` (общая сумма гонораров)

        """
        return self.annotate(
            _time_billed=Sum('billing_item__time_spent'),
            _fees_earned=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                output_field=DecimalField()
            ),
        )

    def aggregate_count_stats(self):
        """ Получите статистику подсчета для дела (по статусу). """
        from . import Matter
        return self.aggregate(
            open_count=Count('pk', filter=Q(status=Matter.STATUS_OPEN)),
            referred_count=Count(
                'pk', filter=Q(status=Matter.STATUS_REFERRAL)
            ),
            closed_count=Count('pk', filter=Q(status=Matter.STATUS_CLOSE)),
            total_count=Count('pk', ),
        )

    def with_time_billings(
        self,
        user: user_models.AppUser,
        period_start: datetime,
        period_end: datetime,
    ):
        """ Добавьте к qs расчетное выставленное время и сборы за определенный период времени.
        Они будут сгруппированы по каждому вопросу.
        """
        return self.available_for_user(user).filter(
            billing_item__date__gte=period_start,
            billing_item__date__lte=period_end
        ).annotate(
            mediator_time_spent=Sum(
                'billing_item__time_spent',
                filter=Q(billing_item__created_by_id=user.pk)
            ),
            time_spent=Sum('billing_item__time_spent'),
            fees=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                output_field=DecimalField()
            ),
            mediator_fees=Sum(
                F('billing_item__rate') * F('billing_item__quantity'),
                filter=Q(billing_item__created_by_id=user.pk),
                output_field=DecimalField()
            ),
        )

    def with_is_shared_for_user(self, user):
        """ Помечайте каждый вопрос флагом "_is_shared".
        Эта аннотация необходима для повышения производительности получения вопросов и
        добавляет флаг, который определяет, является ли вопрос общим для пользователя или нет.

        """
        shared_matters = user.shared_matters.values('id')
        return self.annotate(
            _is_shared=Case(
                When(id__in=shared_matters, then=True),
                default=False,
                output_field=BooleanField()
            )
        )


class BillingItemQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели BillingItem. """

    def match_period(self, period_start: datetime, period_end: datetime):
        """ Отфильтруйте платежный элемент в соответствии с периодом.
        Элемент выставления счета считается соответствующим периоду, если его "дата" 
        находится в период от period_start до period_end.
        """
        return self.filter(date__gte=period_start, date__lte=period_end)

    def calculate_time_billing_for_period(
        self,
        user: user_models.AppUser,
        start_date: datetime,
        end_date: datetime,
    ) -> timedelta:
        """ Рассчитайте время, оплаченное за определенный период времени. """
        return self.available_for_user(
            user
        ).filter(
            date__gte=start_date,
            date__lte=end_date,
        ).aggregate(
            Sum('time_spent')
        ).get('time_spent__sum')

    def get_total_fee(self):
        """ Рассчитайте общую стоимость выставленного счета за время в qs.
        В случае, если qs относится только к одному вопросу, и этот вопрос не имеет
        тип тарифа "почасовая" -> вернуть нет, потому что мы не можем рассчитать общую сумму 
        сборов сумма для таких вопросов.
        """
        # Закомментируйте эту часть для null total_fee
        # проверьте, принадлежит ли исходный qs только к 1 материалу, и проверьте тип его тарифа
        # if self.values('matter').distinct().count() == 1:
        #     # if matter is not hourly rated - return None total `fees` amount
        #     if not self.first().matter.is_hourly_rated:
        #         return
        return sum([obj.fee for obj in self.filter(is_billable=True)])

    def get_total_time(self):
        """ Рассчитайте общее время выставленного счета в qs. """
        time_spent = self.aggregate(Sum('time_spent')) \
            .get('time_spent__sum')

        if not time_spent:
            return '00:00:00'

        return str(time_spent)

    def available_for_editing(self):
        """ Отфильтруйте файлы, которые можно редактировать.
        Только временные счета, прикрепленные к счетам со статусом оплаты
        'not_started' можно отредактировать.
        """
        from . import Invoice
        return self.filter(
            Q(invoices__payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES) |  # noqa
            Q(invoices__isnull=True)
        )

    def with_available_for_editing(self):
        """ Добавьте аннотацию, которая показывает, можно ли ее редактировать или нет. """
        from . import Invoice
        return self.annotate(
            _available_for_editing=Case(
                When(
                    Q(invoices__payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES) |  # noqa
                    Q(invoices__isnull=True),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).distinct()

    def with_is_paid(self):
        """ Добавьте аннотацию, которая показывает, оплачен tb или нет """
        from . import Invoice
        return self.annotate(
            _is_paid=Case(
                When(invoices__status=Invoice.PAYMENT_STATUS_PAID, then=True),
                default=False,
                output_field=BooleanField()
            )
        ).distinct()


class InvoiceQuerySet(AbstractPaidObjectQuerySet, MatterRelatedQuerySet):
    """набор запросов модели Invoice. """

    def match_date(self, date: datetime):
        """ Отфильтруйте счета-фактуры, периоды которых соответствуют "дате`. """
        return self.filter(period_start__lte=date, period_end__gte=date)

    def match_period(self, period_start: datetime, period_end: datetime):
        """ Отфильтруйте счета-фактуры, которые относятся к входному периоду времени.
        Мы возвращаем счета, в которых указан хотя бы один день срока действия
        входной период. Другими словами, мы возвращаем счета-фактуры, которые: имеют period_end
        больше, чем входной period_start, и period_start меньше, чем входной
        period_end. (Если вам трудно это понять, попробуйте нарисовать).

        """
        return self.exclude(
            Q(period_end__lt=period_start) | Q(period_start__gt=period_end)
        )

    def available_for_user(self, user: user_models.AppUser):
        """ Отфильтруйте счета, доступные пользователю.
        Клиент может видеть все счета-фактуры, кроме "ожидающих".
        """
        available_invoices = super().available_for_user(user)
        return available_invoices

    def available_for_editing(self):
        """Счета-фактуры с фильтром можно редактировать.
        Редактировать можно только счета-фактуры со статусом оплаты "не начат"
        """
        from . import Invoice
        return self.filter(
            payment_status__in=Invoice.AVAILABLE_FOR_EDITING_STATUSES
        )

    def with_fees_earned(self):
        """ Рассчитайте заработанные комиссионные за выставление счетов. """
        return self.annotate(
            _fees_earned=Sum(
                F('time_billing__rate') * F('time_billing__quantity'),
                output_field=DecimalField()
            )
        )

    def with_time_billed(self):
        """ Рассчитайте количество оплаченного времени. """
        return self.annotate(
            _time_billed=Sum('time_billing__time_spent')
        )


class MatterPostQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели 'MatterPost`. """


class MatterCommentQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели `MatterComment`. """

    def available_for_user(self, user: user_models.AppUser):
        """ Фильтруйте комментарии в соответствии с доступными пользователю вопросами. """
        from . import Matter
        available_matters = Matter.objects.all().available_for_user(user)
        return self.filter(post__matter__in=available_matters)


class NoteQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели `Note` """

    def available_for_user(self, user: user_models.AppUser):
        """ Переопределенный метод для возврата только созданных пользователем заметок. """
        qs = super().available_for_user(user)
        return qs.filter(
            Q(created_by=user) |
            Q(matter__mediator__user=user) |
            Q(matter__client__user=user)
        )


class VoiceConsentQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели `VoiceConsent`. """


class VideoCallQuerySet(QuerySet):
    """ набор запросов модели `VideoCall`. """

    def available_for_user(self, user: user_models.AppUser):
        """ Получать видеозвонки: созданные пользователем или куда пользователь был приглашен. """
        return self.filter(participants=user)

    def get_by_participants(self, participants):
        """ Получите звонок по списку участников. """
        video_call_qs = self.annotate(
            participants_count=Count('participants')
        ).filter(
            participants_count=len(participants)
        )
        video_calls = reduce(
            lambda qs, pk: qs.filter(participants=pk),
            participants,
            video_call_qs
        )
        return video_calls.first()


class MatterSharedWithQuerySet(MatterRelatedQuerySet):
    """ набор запросов модели `MatterSharedWith`. """
