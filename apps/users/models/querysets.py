import logging
import typing
from datetime import datetime
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import models
from django.db.models import Count, Q, Sum
from ...finance.models.payments.querysets import AbstractPaidObjectQuerySet
from .utils.verification import VerifiedRegistrationQuerySet


__all__ = (
    'InviteQuerySet',
    'MediatorQuerySet',
    'ClientQuerySet',
    'AppUserQuerySet',
    'SupportQuerySet',
)


logger = logging.getLogger('django')


class InviteQuerySet(models.QuerySet):
    """Queryset class for `Invite` model."""

    def without_user(self):
        """ Возвращать приглашения без участия пользователя. """
        return self.filter(user__isnull=True)

    def without_matter(self):
        """Return invites without matter."""
        return self.filter(matter__isnull=True)

    def only_invited_type(self):
        """ Фильтруйте приглашения только по типу `invited_by_user`. """
        from . import Invite
        return self.filter(type=Invite.TYPE_INVITED)


class AppUserQuerySet(models.QuerySet):
    """Queryset class for `AppUser` model."""

    def available_for_share(self, matter=None):
        """ Получите набор запросов, доступных для совместного использования пользователями.
        Это:
            - проверенные адвокаты с активной подпиской
            - проверенные помошники адвокатов
        Если определено "значение" - удалите уже совместно используемых адвокатов из qs.
        """
        from . import Mediator
        #mediators = Mediator.objects.verified() \
        #    .has_active_subscription().values_list('pk', flat=True)
        mediators = Mediator.objects.verified().values_list('pk', flat=True)

        available = self.exclude(is_staff=True).filter(
            models.Q(id__in=mediators)
        )

        if not matter:
            return available

        available = set(available.values_list('id', flat=True))
        already_shared = set(matter.shared_with.values_list('id', flat=True))
        return self.filter(id__in=available - already_shared)

    def shared_to_matter(self, matter):
        """ Получить набор запросов пользователей, совместно используемых для matter
            плюс главный юрист matter.
        """
        matter_shared_users = set(
            matter.shared_with.values_list('id', flat=True))
        return self.filter(
            id__in=matter_shared_users.union(set([matter.mediator.user.id])))

    def active(self):
        """ Получите набор запросов только от `активных` пользователей приложения. """
        return self.filter(is_active=True)

    def mediators(self):
        """ Получите набор запросов пользователей приложения, которые являются 
        только проверенными адвокатами. """
        from . import Mediator
        #mediators = Mediator.objects.real_users().verified() \
        #    .has_active_subscription()
        #return self.filter(id__in=mediators.values_list('user__id', flat=True))

    def clients(self):
        """ Получите набор запросов пользователей клиентов. """
        return self.filter(client__isnull=False)

    def support(self):
        """ Получите набор запросов от проверенных пользователей приложения поддержки. """
        from . import Support

        support = Support.objects.verified().paid()
        return self.filter(id__in=support.values_list('user__id', flat=True))

    def exclude_staff(self):
        """ Удалите менеджеров из набора запросов. """
        return self.exclude(is_staff=True)

    def is_registered(self, email):
        """ Проверьте электронную почту, если она уже существует """
        return self.filter(email__iexact=email).exists()


class MediatorQuerySet(VerifiedRegistrationQuerySet):
    """Queryset class for `Mediator` model."""

    def with_distance(
        self,
        longitude: typing.Union[int, float, str],
        latitude: typing.Union[int, float, str],
    ):
        """ Добавьте аннотацию расстояния в набор запросов помощника юриста.
        Если отправлены неверные координаты, метод аннотирует набор запросов с помощью
        расстояние = null. Мы не можем просто вернуть queryset(self), потому что мы
        позже в api используйте "distance" для заказа помощников юриста.
        """
        try:
            point = Point(
                x=float(longitude),
                y=float(latitude),
                srid=settings.LOCATION_SRID,
            )
        except (TypeError, ValueError) as error:
            return self.annotate(
                distance=models.Value(None, output_field=models.FloatField())
            )
        return self.annotate(
            distance=Distance('firm_location', point)
        )

    def has_lead_with_user(self, user):
        """ Отфильтруйте адвокатов, с которыми у клиента есть контакты.
        Если пользователь является клиентом, мы фильтруем набор запросов, чтобы вернуть 
        только этого клиента есть зацепка с.
        """
        if user.is_client:
            return self.filter(leads__client_id=user.pk)
        return self

    def real_users(self):
        """ Возвращайте адвокатов, которые не являются штатными пользователями. """
        return self.filter(user__is_staff=False)

    def has_active_subscription(self):
        """ Возвращайте адвокатов с активной подпиской. """
        return True
        return self.exclude(user__active_subscription__isnull=True)

    def aggregate_count_stats(self):
        """ Получите статистику подсчета голосов для адвоката (по статусу подтверждения). """
        from . import Mediator
        return self.aggregate(
            verified_count=Count(
                'pk', filter=Q(
                    verification_status=Mediator.VERIFICATION_APPROVED
                )
            ),
            not_verified_count=Count(
                'pk', filter=Q(
                    verification_status=Mediator.VERIFICATION_NOT_VERIFIED
                )
            ),
            total_count=Count('pk', ),
        )

class EnterpriseQuerySet(VerifiedRegistrationQuerySet):
    """Queryset class for `Enterprise` model."""

    def real_users(self):
        """ Возвращайте предприятия, которые не являются менеджерами. """
        return self.filter(user__is_staff=False)

    def aggregate_count_stats(self):
        """ Получите статистику подсчета для предприятия (по статусу проверки). """
        from . import Enterprise
        return self.aggregate(
            verified_count=Count(
                'pk', filter=Q(
                    verification_status=Enterprise.VERIFICATION_APPROVED
                )
            ),
            not_verified_count=Count(
                'pk', filter=Q(
                    verification_status=Enterprise.VERIFICATION_NOT_VERIFIED
                )
            ),
            total_count=Count('pk', ),
        )


class ClientQuerySet(models.QuerySet):
    """Queryset class for `Client` model."""

    def has_lead_with_user(self, user):
        """ Отфильтруйте клиентов, с которыми у адвоката есть контакты.
        Если пользователь является адвокатом, мы фильтруем набор запросов, чтобы вернуть 
        клиентов, с которыми у адвоката есть лид.
        """
        if user.is_mediator:
            return self.filter(leads__mediator_id=user.pk)
        return self

    def has_matter_with_user(self, user, matter_statuses=None):
        """ Отфильтруйте клиентов, с которыми у адвоката есть проблемы.
        Если пользователь является адвокатом, мы фильтруем набор запросов, чтобы возвращать 
        клиентов, с которыми у адвоката есть дело (со статусами ввода).

        Если пользователь является общим адвокатом или службой поддержки, мы фильтруем набор 
        запросов для возврата клиенты из общих с ними вопросов (со статусами ввода).
        """
        from ...business.models import Matter

        if not matter_statuses:
            matter_statuses = (Matter.STATUS_OPEN, Matter.STATUS_CLOSE)

        if user.is_client:
            return self

        return self.filter(
            # фильтровать клиентов, у которых есть вопросы к текущему адвокату пользователя
            Q(matters__mediator_id=user.pk) |
            # фильтруйте клиентов по общим вопросам с текущим адвокатом пользователя или
            # support
            Q(matters__shared_links__user_id=user.pk),
            # ограничивать статусы
            matters__status__in=matter_statuses
        ).distinct()

    def invited_by_user(self, user):
        """ Получите клиентов, которые были приглашены пользователем. """
        return self.filter(user__invitations__inviter_id=user.pk).distinct()

    def user_clients(self, user):
        """ Привлекайте клиентов-адвокатов.
        Клиенты адвоката - это клиенты, которые:
            Были приглашены адвокатом
            Есть вопросы к адвокату
            Есть лиды у адвоката
            Поделились своими проблемами с адвокатом
        """

        if not user.is_mediator:
            return self

        matter_filter = Q(matters__mediator_id=user.pk)
        lead_filter = Q(leads__mediator_id=user.pk)
        invite_filter = Q(user__invitations__inviter_id=user.pk)
        shared_matter_filter = Q(matters__shared_links__user_id=user.pk)

        return self.filter(
            matter_filter | shared_matter_filter | lead_filter | invite_filter
        ).distinct()


class SupportQuerySet(
    AbstractPaidObjectQuerySet, VerifiedRegistrationQuerySet
):
    """Queryset class for `Support` model."""


class UserStatisticsQuerySet(models.QuerySet):
    """Queryset class for `UserStatistics` model."""

    def for_period(
        self,
        user,
        start_date: datetime,
        end_date: datetime
    ):
        """ Получите статистику за определенный период времени. """
        return self.filter(
            user=user, created__gte=start_date, created__lte=end_date
        )

    def stats_count_for_tag(
        self,
        user,
        tag: str,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """ Получите статистику за определенный период времени по тегу. """
        count = self.for_period(
            user=user, start_date=start_date, end_date=end_date
        ).filter(tag=tag).aggregate(Sum('count'))['count__sum']
        if not count:
            return 0
        return count
