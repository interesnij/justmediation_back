import random
import string
import uuid
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from apps.core.models import BaseModel
from ...users.models.users import AppUser
from ...users.models.mediators import Mediator
from ...users.models.clients import Client
from ...users.models.enterprise import Enterprise
from ...users.models.invites import Invite
from ...users.models.extra import *
from .querysets import LeadQuerySet, MatterQuerySet, OpportunityQuerySet
from apps.forums.models import Post

__all__ = (
    'Opportunity',
    'Lead',
    'Matter',
)


def create_matter_code():
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(24)
    )


class Opportunity(BaseModel):
    """
    Активный чат (контакт) между адвокатом и потенциальным клиентом

    Атрибуты:
        client (Client): ссылка на клиента, участвовавшего в контакте
        mediator (Mediator): ссылка на адвоката, участвовавшего в контакте
        chat_channel (str): идентификатор Firestore соответствующего чата
        priority (str): приоритет, который адвокат устанавливает для этого чата

        ЗАДАЧА: Более подробная информация будет добавлена позже в соответствии с
        к требованиям/потоку для преобразования.
    """

    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low'))
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='opportunities'
    )
    mediator = models.ForeignKey(
        Mediator,
        on_delete=models.PROTECT,
        verbose_name=_('Mediator'),
        related_name='opportunities'
    )
    chat_channel = models.UUIDField(
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )

    priority = models.CharField(
        max_length=10,
        verbose_name=_('Opportunity Priority'),
        null=True,
        blank=True,
        choices=PRIORITY_CHOICES,
    )
    objects = OpportunityQuerySet.as_manager()


class Lead(BaseModel):
    """ Активный чат (контакт) между адвокатом и клиентом

    Новый лид создается из открытых тем, и это означает, что
    Адвокат и клиент хотят провести несколько дискуссий на
    соответствующую тему и решить, хотят ли они начать
    `matter` (deal) вместе.

    Атрибуты:
        post (Post): ссылка на сообщение, в котором был инициирован контакт между клиентом и
        адвокатом
        client (Client): ссылка на клиента, участвовавшего в контакте
        mediator (Mediator): ссылка на адвоката, участвовавшего в контакте
        priority (str): приоритет, который адвокат устанавливает для этого чата
        chat_channel (str): идентификатор Firestore соответствующего чата
        status (str):
            Текущий статус вывода, он может быть: "активен" или "преобразован"
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low'))
    )

    post = models.ForeignKey(
        Post,
        # адвокат, способный инициировать контакт не только по возможности/теме
        on_delete=models.SET_NULL,
        verbose_name=_('Post'),
        related_name='leads',
        null=True,
        blank=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='leads'
    )
    mediator = models.ForeignKey(
        Mediator,
        on_delete=models.SET_NULL,
        verbose_name=_('Mediator'),
        related_name='leads',
        null=True
    )
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.SET_NULL,
        verbose_name=_('Enterprises'),
        related_name='leads',
        null=True
    )
    priority = models.CharField(
        max_length=10,
        verbose_name=_('Lead Priority'),
        null=True,
        blank=True,
        choices=PRIORITY_CHOICES,
    )
    chat_channel = models.UUIDField(
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )

    STATUS_ACTIVE = 'active'
    STATUS_CONVERTED = 'converted'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_CONVERTED, _('Converted')),
    )

    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status')
    )

    objects = LeadQuerySet.as_manager()

    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        unique_together = ('client', 'mediator')

    def __str__(self):
        return f'Chat between {self.client} and {self.mediator}'

    @property
    def is_converted(self):
        """ Проверьте, преобразован ли lead."""
        return self.status == self.STATUS_CONVERTED


class Matter(BaseModel):
    """Matter

    Представляет собой рабочие отношения между адвокатом и Клиентом, своего рода
    соглашение с заранее определенной ставкой, видом работы и т.д.

    Атрибуты:
        lead (Lead): ссылка на контакт (чат), с помощью которого был создан материал
        client (Client): ссылка на клиента - заказчика matter
        mediator (Mediator): ссылка на адвоката, который работает по данному вопросу
        code (str): специальный буквенный код (идентификатор)
        title (str): название вопроса
        description (текст): простое описание вопроса простыми словами
        rate (decimal): сумма, принимаемая по типу ставки в долларах
        country (Country): страна юрисдикции по данному вопросу
        state (Region): государство юрисдикции по данному вопросу
        city (City): город, в юрисдикции которого находится дело
        status (str): текущее состояние вопроса, открыто оно или закрыто
        stage (Stage): стадия рассмотрения индивидуального дела, созданная адвокатом
        completed (datetime): временная метка, когда вопрос был закрыт
        shared_with (AppUser): список пользователей, с которыми осуществляется общий доступ к данным
        referral (Referral): Запрос на направление от другого адвоката
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    Существуют следующие возможные биллинговые системы:

        1. Почасовая ставка = `тариф` * количество выставленных часов -> система создает
        счет-фактуру

        2. Фиксированная установленная сумма = `ставка` для записи -> счет не генерируется
        (адвокат все еще тратит время на отслеживание конфликтов)

        3. Плата за непредвиденные расходы = "ставка" для записи -> счет не сгенерирован
        (адвокат все еще тратит время на отслеживание конфликтов)

        4. Альтернативное соглашение = `тариф` для записи -> счет-фактура не сгенерирована
        (адвокат все еще тратит время на отслеживание конфликтов)

    """

    # ЗАДАЧА: уточнить ограничения на обновления статусов
    # переход к статусам осуществляется с помощью простых кнопок на стороне интерфейса
    STATUS_OPEN = 'open'
    STATUS_REFERRAL = 'referral'
    STATUS_CLOSE = 'close'

    STATUS_CHOICES = (
        (STATUS_OPEN, _('Open')),
        (STATUS_REFERRAL, ('Referral')),
        (STATUS_CLOSE, _('Close')),
    )

    STATUS_TRANSITION_MAP = {
        STATUS_OPEN: 'open',
        STATUS_REFERRAL: 'referral',
        STATUS_CLOSE: 'close',
    }

    lead = models.ForeignKey(
        'business.Lead',
        # matter может существовать без лида, поэтому его можно легко удалить
        on_delete=models.SET_NULL,
        verbose_name=_('Lead'),
        related_name='matters',
        null=True,
        blank=True
    )
    invite = models.ForeignKey(
        Invite,
        verbose_name=_('Invite'),
        related_name='matters',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='matters',
        null=True,
        blank=True,
    )
    mediator = models.ForeignKey(
        Mediator,
        on_delete=models.SET_NULL,
        verbose_name=_('Mediator'),
        related_name='matters',
        null=True
    )
    referral_ignore_mediator = models.ForeignKey(
        Mediator,
        on_delete=models.SET_NULL,
        verbose_name=_('Referral Ignore Mediator'),
        related_name='referral_ignored_matters',
        null=True,
        default=None
    )
    
    code = models.CharField(
        max_length=25,
        verbose_name=_('Code'),
        help_text=_('Simple alphabetical code (identifier) of a matter'),
        default=create_matter_code
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Start date")
    )
    close_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Close date")
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Extra matter description')
    )
    speciality = models.ForeignKey(Speciality,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True,
                                   verbose_name=_("Speciality"))
    currency = models.ForeignKey(
        Currencies,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Currency")
    )

    rate = models.DecimalField(
        max_digits=30,
        decimal_places=2,
        verbose_name=_('Rate'),
        help_text=_('Amount of money taken for a rate type in $'),
        default=0
    )
    rate = models.CharField(
        max_length=50,
        verbose_name=_('Rate'),
        help_text=_('Amount of money taken for a rate type in $'),
    )
    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('Country'),
        null=True,
        blank=True
    )
    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('State'),
        null=True,
        blank=True
    )
    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        related_name='matters',
        verbose_name=_('City'),
        null=True,
        blank=True
    )
    is_billable = models.BooleanField(
        default=False,
        verbose_name=_("Is billable")
    )
    fee_type = models.ForeignKey(
        FeeKind,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Fee type")
    )
    fee_note = models.TextField(
        default='',
        max_length=255,
        verbose_name='Fee note'
    )

    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        # default=STATUS_DRAFT,
        default=STATUS_OPEN,
        verbose_name=_('Status')
    )
    stage = models.ForeignKey(
        'Stage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Stage'),
        related_name='matters',
    )
    completed = models.DateTimeField(
        verbose_name=_('Completed datetime'),
        help_text=_('Datetime when the matter was completed(closed)'),
        null=True,
        blank=True
    )
    shared_with = models.ManyToManyField(
        to=AppUser,
        related_name='shared_matters',
        through='MatterSharedWith',
        verbose_name=_('Shared with'),
        help_text=_('Users with which matter is shared')
    )
    referral = models.ForeignKey(
        'Referral',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Referral'),
        related_name='matters',
    )

    objects = MatterQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter')
        verbose_name_plural = _('Matters')
        unique_together = ['mediator', 'code']
        constraints = [
            models.CheckConstraint(
                check=Q(client__isnull=False) | Q(invite__isnull=False),
                name='One of the client or invite should not be null'
            )
        ]

    def __str__(self):
        return f'{self.title}'

    def clean_code(self):
        """ Убедитесь, что код уникален для mediator. """
        self.code = self.code.upper()
        duplicate = self.__class__.objects.filter(
            code=self.code, mediator_id=self.mediator_id,
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'Matter with code:`{self.code}` is already exist'
            )

    def clean_lead(self):
        """ Проверьте данные о лидах.
        Убедитесь, что значение `адвокат` совпадает с соответствующим lead.
        """
        if not self.lead_id:
            return

        if self.mediator_id != self.lead.mediator_id:
            raise ValidationError(_(
                "Matter's `mediator` doesn't match from matter's lead"
            ))

    def clean_stage(self):
        """ Проверьте, принадлежит ли стадия адвокату дела. """
        if not self.stage_id:
            return

        if self.stage.mediator_id != self.mediator_id:
            raise ValidationError(_(
                "Stage doesn't belong to this mediator"
            ))

    def can_change_status(self, user):
        """ Верните `True`, если `пользователь` может изменить "статус` объекта.
        Статус дела может быть изменен только первоначальным "адвокатом" дела или
        пользователи, с которыми был предоставлен общий доступ к этому вопросу.
        """
        return user.pk == self.mediator_id or self.is_shared_for_user(user)

    def is_shared_for_user(self, user):
        """Возвращает `True`, если дело является общим для пользователя. """
        if hasattr(self, '_is_shared'):
            return self._is_shared
        return bool(self.shared_with.filter(id=user.id).exists())

    def delete_referral(self):
        """
         Удалите объект направления, относящийся к делу, после утверждения адвокатом
        """
        if self.status == Matter.STATUS_REFERRAL:
            if settings.F_DOMAIN != "":
                import requests
                from django.conf import settings
                requests.post(settings.F_DOMAIN + 'delete_matter_user', json={
                    "token": settings.OUT_TOKEN,
                    "item_id": self.id,
                    "user_id": self.referral.mediator.id
                })

            self.mediator = self.referral.mediator
            self.referral.delete()
            self.referral = None

    @property
    def referral_pending(self):
        """
        Возвращает `True`, если пользователь отправляет реферал
        
        """
        #return self.referral.mediator.user
        return True

    @property
    def referral_ignored(self):
        return bool(self.referral_ignore_mediator)

    @property
    def referral_request(self):
        """ Возвращает `True`, если пользователь получает реферал """
        # return self.mediator.user
        return True

    @property
    def is_open(self):
        """ Укажите, имеет ли дело статус `открыто`. """
        return self.status == Matter.STATUS_OPEN

    @transition(field=status,
                target=STATUS_OPEN,
                permission=can_change_status)
    def open(self, user=None):
        """ Обновите статус дела до "открыто". """
        # Избежать ошибки импорта
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        import requests
        from django.conf import settings

        if self.referral is not None:
            if settings.F_DOMAIN != "":
                requests.post(settings.F_DOMAIN + 'delete_matter_user', json={
                    "token": settings.OUT_TOKEN,
                    "item_id": self.id,
                    "user_id": self.referral.mediator.id
                })
            self.referral.delete()
            self.referral = None
        create_stat(
            user=self.mediator.user, tag=UserStatistic.TAG_OPEN_MATTER
        )
        if settings.F_DOMAIN != "":
                requests.post(settings.F_DOMAIN + 'open_matter', json={
                "token": settings.OUT_TOKEN,
                "item_id": self.id
            })

    @transition(field=status,
                source=STATUS_OPEN,
                target=STATUS_REFERRAL,
                permission=can_change_status)
    def send_referral(self, user=None):
        """ Обновите статус дела до "открыто". """
        # Избежать ошибки импорта
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        create_stat(
            user=self.mediator.user, tag=UserStatistic.TAG_REFERRED_MATTER
        )

    @transition(field=status,
                source=STATUS_REFERRAL,
                target=STATUS_OPEN,
                permission=can_change_status)
    def accept_referral(self, user=None):
        """ Обновите статус дела до "открыто". """
        # Избежать ошибки импорта
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        create_stat(
            user=self.mediator.user, tag=UserStatistic.TAG_OPEN_MATTER
        )

    @transition(field=status,
                source=STATUS_REFERRAL,
                target=STATUS_OPEN,
                permission=can_change_status)
    def ignore_referral(self, user):
        """ Обновите статус дела до "открыто". """
        # Избежать ошибки импорта
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        if self.referral is not None:
            if settings.F_DOMAIN != "":
                import requests
                from django.conf import settings
                requests.post(settings.F_DOMAIN + 'delete_matter_user', json={
                    "token": settings.OUT_TOKEN,
                    "item_id": self.id,
                    "user_id": user.id
                })

            self.referral.delete()
            self.referral = None
            self.referral_ignore_mediator = user.mediator
        create_stat(
            user=self.mediator.user, tag=UserStatistic.TAG_OPEN_MATTER
        )

    @transition(field=status,
                source=STATUS_REFERRAL,
                target=STATUS_OPEN,
                permission=can_change_status)
    def revoke_referral(self):
        """ Обновите статус дела до "открыто". """
        if self.referral is not None:
            if settings.F_DOMAIN != "":
                import requests
                from django.conf import settings
                requests.post(settings.F_DOMAIN + 'delete_matter_user', json={
                    "token": settings.OUT_TOKEN,
                    "item_id": self.id,
                    "user_id": self.referral.mediator.id
                })

            self.referral.delete()
            self.referral = None

    @transition(field=status,
                source=STATUS_OPEN,
                target=STATUS_CLOSE,
                permission=can_change_status)
    def close(self, user=None):
        """ Обновите статус вопроса до `закрыть`.
        Также добавьте статистику по закрытым вопросам к адвокату.
        """
        # Избежать ошибки импорта
        from ...users.models import UserStatistic
        from ...users.services import create_stat
        import requests
        from django.conf import settings

        if self.referral is not None:
            if settings.F_DOMAIN != "":
                requests.post(settings.F_DOMAIN + 'delete_matter_user', json={
                    "token": settings.OUT_TOKEN,
                    "item_id": self.id,
                    "user_id": self.referral.mediator.id
                })
            self.referral.delete()
            self.referral = None
        create_stat(
            user=self.mediator.user, tag=UserStatistic.TAG_CLOSE_MATTER
        )
        self.close_date = date.today()
        if settings.F_DOMAIN != "":
                requests.post(settings.F_DOMAIN + 'close_matter', json={
                "token": settings.OUT_TOKEN,
                "item_id": self.id
            })

    @property
    def time_billed(self) -> timedelta:
        """ Возвращает сумму `затраченного времени` в журналах заданий. """
        # попробуйте получить уже вычисленные из значений qs `with_totals` значения qs
        if hasattr(self, '_time_billed'):
            return self._time_billed

        time_billed = self.billing_item.aggregate(Sum('time_spent'))
        return time_billed['time_spent__sum']

    @property
    def fees_earned(self) -> timedelta or None:
        """ Возвращает сумму "сборов" за материалы в журналах заданий. """
        # если значение не является "почасовым", верните значение None
        if not self.is_hourly_rated:
            return

        # попробуйте получить уже вычисленные из значений qs `with_totals` значения qs
        if hasattr(self, '_fees_earned'):
            return self._fees_earned

        fees_earned = sum([obj.fee for obj in self.billing_item.all()])
        return fees_earned

    @property
    def is_hourly_rated(self) -> bool:
        """ Возвращает true, если значение имеет "почасовой" `rate_type`. """
        return self.fee_type is not None and self.fee_type.id == 3

    def save(self, **kwargs):
        """ Сохраните код в верхнем регистре. """
        self.code = self.code.upper()
        super().save(**kwargs)

    @classmethod
    def get_by_invite(cls, invite):
        return cls.objects.filter(
            invite=invite
        )
