import datetime
import decimal
import logging
import traceback
from datetime import timedelta
from decimal import Decimal
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import stripe
from dirtyfields import DirtyFieldsMixin
from django_fsm import FSMField, transition
from libs.django_fcm.exceptions import TransitionFailedException
from ...core.models import BaseModel
from ...finance.models.payments.payments import AbstractPaidObject
from .extra import Attachment, PaymentMethods
from .querysets import BillingItemQuerySet, InvoiceQuerySet
from ...users.models.users import AppUser
from ...users.models.extra import Currencies

__all__ = (
    'BillingItem',
    'Invoice',
    'BillingItemAttachment',
)

from ...users.models import Client

logger = logging.getLogger('django')


class BillingItem(DirtyFieldsMixin, BaseModel):
    """ BillingItem.

    Эта модель отражает количество времени, затраченного адвокатом на соответствующие
    вопрос (вид регистрации времени).

    Атрибуты:
        matter (Matter): вопрос, в котором выставляется счет за работу
        created_by (AppUser): пользователь приложения, который создал выставление счета за время
        invoices  (BillingItemAttachment): счета-фактуры, к которым подключена эта оплаченная 
        работа.
        description (текст): описанная работа человеческими словами
        date (date): дата, в которую была выполнена оплаченная работа.
        time_spent (продолжительность): количество времени, затраченного адвокатом на работу
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз
        billing_type (варианты текста): Представляет тип выставления счетов, это может быть
        expense: Если выставление счетов производится за объем
            время: Если выставляется счет за зарегистрированное время
        is_billable (bool): если ввод времени оплачивается
        client (Client): клиент, с которого будет снято обвинение
        hourly_rate (десятичная): почасовая ставка, которая взимается, если это запись времени
        quantity (int): Количество, если это запись расхода
        rate (десятичная): Цена единицы измерения, если ее расходная запись
        attachment (поле файла): Требуется вложение, если тип выставления счета - расход
    """
    attachments = models.ManyToManyField(
        Attachment,
        verbose_name=_('File'),
        help_text=_("Billing item attachments"),
    )
    is_billable = models.BooleanField(
        default=False,
        verbose_name=_('Is billable entry'),
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='billed_item',
        verbose_name=_('Client'),
        null=True
    )
    matter = models.ForeignKey(
        'Matter',
        verbose_name=_('Matter'),
        related_name='billing_item',
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        AppUser,
        #editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser created time billing'),
        related_name='billing_item',
        on_delete=models.PROTECT,
    )
    billed_by = models.ForeignKey(
        AppUser,
        verbose_name=_('Billed by'),
        related_name='billed_item',
        on_delete=models.PROTECT,
        null=True
    )
    invoices = models.ManyToManyField(
        'Invoice',
        verbose_name=_('Invoices'),
        through='BillingItemAttachment',
        related_name='time_billing',
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Full description of made work')
    )
    time_spent = models.DurationField(
        verbose_name=_('Time Spent'),
        help_text=_('Amount of time that mediator spent on this work'),
        validators=[
            validators.MinValueValidator(datetime.timedelta(minutes=15)),
            validators.MaxValueValidator(datetime.timedelta(hours=24)),
        ],
        null=True,
        blank=True
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Hourly rate'),
        help_text=_('Hourly rate for which time entry is added'),
        default=0
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Rate'),
        help_text=_('Unit rate for which expense entry is added'),
        null=True,
        default=None
    )
    quantity = models.PositiveIntegerField(
        verbose_name=_('Quantity'),
        help_text=_('Quantity of the item for which expense entry is added'),
        null=True,
        default=None
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total amount'),
        help_text=_('Total amount for which expense entry is added'),
        default=0
    )
    currency = models.ForeignKey(
        Currencies,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Currency")
    )
    date = models.DateField(
        verbose_name=_('Date'),
        help_text=_('Date in which billed work was made')
    )
    BILLING_TYPE_EXPENSE = 'expense'
    BILLING_TYPE_TIME = 'time'
    BILLING_TYPE_FLAT_FEE = 'flat_fee'
    BILLING_TYPES = (
        (BILLING_TYPE_EXPENSE, _('Expense')),
        (BILLING_TYPE_TIME, _('Time')),
        (BILLING_TYPE_FLAT_FEE, _('Flat fee'))
    )

    billing_type = models.CharField(
        choices=BILLING_TYPES,
        max_length=10,
        default=BILLING_TYPE_TIME,
        verbose_name=_("Billing Type")
    )

    objects = BillingItemQuerySet.as_manager()

    class Meta:
        verbose_name = _('Billing Item')
        verbose_name_plural = _('Billing Item')

    def __str__(self):
        return f'{self.description[:5]} @ {self.matter}'

    @property
    def available_for_editing(self) -> bool:
        """ Проверьте, связано ли выставление счета за время с выставлением счета только для чтения ."""
        if hasattr(self, '_available_for_editing'):
            return self._available_for_editing
        if not self.invoices.all().exists():
            # Это для случая, когда tb новый и он не прикреплен ни к одному счету-фактуре
            return True
        return self.invoices.available_for_editing().exists()

    @property
    def fee(self) -> float:
        """ Рассчитайте плату в зависимости от времени и расходов """
        amount = 0
        if self.billing_type == BillingItem.BILLING_TYPE_TIME:
            if self.time_spent is not None:
                amount = float(self.hourly_rate) * \
                    self.time_spent.total_seconds() / 3600
        else:
            amount = float(self.total_amount)
        return amount

    @classmethod
    def mediator_billing_items(cls, matters):
        return cls.objects.filter(matter__in=matters)

    @property
    def is_billed(self) -> bool:
        """ Проверьте, прикреплен ли платежный элемент к счету-фактуре. """
        return self.billing_items_invoices.count() > 0


class TimeEntry(BaseModel):
    start_time = models.DateTimeField(
        verbose_name=_('Start time')
    )
    end_time = models.DateTimeField(
        null=True,
        verbose_name=_('End time')
    )
    billing_item = models.ForeignKey(
        BillingItem,
        on_delete=models.CASCADE,
        verbose_name=_('Billing Item'),
        related_name='time_entries',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        AppUser,
        #editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser created time billing'),
        related_name='time_entries',
        on_delete=models.PROTECT,
        null=True
    )

    @classmethod
    def calculate_elapsed_time(cls, created_by, billing_item):
        time_entries = cls.objects.filter(created_by=created_by)
        if billing_item:
            time_entries = time_entries.filter(billing_item=billing_item)
        else:
            time_entries = time_entries.filter(billing_item__isnull=True)
        is_running = False
        time_elapsed = timedelta()
        for time_entry in time_entries:
            start = time_entry.start_time
            end = time_entry.end_time or timezone.now()
            time_elapsed += end - start
            if time_entry.end_time is None:
                is_running = True
        return time_elapsed, is_running

    @classmethod
    def elapsed_time_without_microseconds(cls, created_by, billing_item):
        elapsed_time_exact, is_running = cls.calculate_elapsed_time(
            created_by,
            billing_item
        )
        return str(elapsed_time_exact).split('.')[0], is_running

    @classmethod
    def get_running_time_entry(cls, created_by, billing_item):
        time_entries = cls.objects.filter(
            created_by=created_by,
            end_time__isnull=True
        )
        if billing_item:
            time_entries = time_entries.filter(billing_item=billing_item)
        else:
            time_entries = time_entries.filter(billing_item__isnull=True)

        return time_entries.order_by(
            '-created'
        ).first()


class BillingItemAttachment(BaseModel):
    """Many-to-many связь между платежными позициями и счетами-фактурами

    Attributes:
        billing_items (BillingItem): Внешний ключ для элемента выставления счета
        invoice (Invoice): Внешний ключ для счета-фактуры

    """
    time_billing = models.ForeignKey(
        'BillingItem',
        verbose_name=_('Time Billing'),
        on_delete=models.CASCADE,
        related_name='attached_invoice',
    )
    invoice = models.ForeignKey(
        'Invoice',
        verbose_name=_('Invoice'),
        on_delete=models.CASCADE,
        related_name='attached_time_billing'
    )

    class Meta:
        verbose_name = _('Attached Time Billing')
        verbose_name_plural = _('Attached Time Billings')

    @property
    def available_for_editing(self) -> bool:
        """ Проверьте, относится ли вложение для выставления счета за время к счету 
        только для чтения. """
        return self.invoice.available_for_editing

    @property
    def is_paid(self) -> bool:
        """ Проверьте, связано ли вложение для выставления счета за время с оплаченным счетом. """
        return self.invoice.is_paid

    def __str__(self):
        return (
            f'#{self.id}. Time billing #{self.time_billing_id} attached to '
            f'Invoice #{self.invoice_id}-{self.invoice.title}'
        )

    def clean_invoice(self):
        """ Очистите экземпляры вложений элементов выставления счетов. """
        if self.time_billing.matter_id != self.invoice.matter_id:
            raise ValidationError(_(
                "Invoice's `matter` doesn't match BillingItem `matter`"
            ))

        if not self.invoice.matter.is_hourly_rated:
            raise ValidationError(_(
                "It's not allowed to attach time billings with invoices for "
                "not `hourly` rated matters"
            ))

        if (
            self.invoice.period_start > self.time_billing.date or
            self.invoice.period_end < self.time_billing.date
        ):
            raise ValidationError(_(
                "Time Billing date is not from selected invoice time period."
            ))


class Invoice(AbstractPaidObject, DirtyFieldsMixin, BaseModel):
    """Invoice
    Эта модель представляет собой сумму денег, которую клиент должен заплатить за
    Услуги адвоката в определенные сроки.

    Счета-фактуры отправляются только тем клиентам, у которых тип тарифа "почасовая".

    Атрибуты:
    number (str): номер счета-фактуры из stripe
    invoice_id (str): идентификатор счета-фактуры из stripe
    client (Client): это клиент, для которого рассчитывается счет-фактура.
    matter (Matter): вопрос, по которому рассчитывается счет-фактура.
    billing_items (BillingItems): являются ли элементы выставления счетов в счете-фактуре
    period_start (date): дата начала расчета счета-фактуры.
    period_end (date): дата окончания, до которой рассчитывается счет-фактура.
    title (str): название счета-фактуры (например, за какие услуги)
    
    status (str): текущий статус счета-фактуры, это может быть:
    ожидающий, отправленный, payment_in_progress, payment_failed и оплаченный.
    Pending -> Установить при создании счета-фактуры. Клиент не может быть замечен.
    Sent -> Установить, когда счет отправляется клиенту или когда платеж
    отменяется.
    Payment in progress -> Установить, когда клиент начнет оплачивать
    invoice (когда интерфейс запрашивает payment_intent) или возобновление платежа
    процесс.
    Payment failed -> Установить, когда не удалось произвести оплату по счету. Неудачный
    оплата счета по-прежнему может быть оплачена и отмечена как оплаченная
    Paid -> Установить оплату по счету-фактуре успешно.
    
    Статусы, когда адвокат может редактировать счет-фактуру и связанные с ней
    счета за время -> Ожидающие и отправленные
    Статусы, когда адвокат не может отредактировать счет-фактуру и связанные с ней
    выставление счетов за время -> Оплата в процессе или оплачена
    Вы можете узнать, можете ли вы редактировать или нет, проверив
    свойство `available_for_editing`
    
    note (str): адвокат может оставить примечание при отправке счета-фактуры
    payment_method (PaymentMethods): Способ оплаты для выполнения платежа
    payment (Payment): Ссылка на объект платежа, все платежи по счету-фактуре
    created_by (AppUser): Пользователь, создавший счет-фактуру, в задаче celery он установлен
        владельцу matter'а
    created (datetime): временная метка, когда был создан экземпляр
    modified (datetime): временная метка, когда экземпляр был изменен в последний раз
    due_date (дата): Представляет дату оплаты счета-фактуры
    due_days (int): Количество дней оплаты
    email (email): электронная почта клиента
    finalized (datetime): временная метка, когда экземпляр был завершен
    activities (InvoiceActivity): действия по выставлению счета
    logs (InvoiceLog): журналы выставления счетов
    """
    number = models.CharField(
        verbose_name=_('Invoice Number'),
        max_length=15,
        null=True
    )
    invoice_id = models.CharField(
        verbose_name=_('Invoice ID'),
        max_length=30,
        null=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='invoices',
        null=True,
        blank=True
    )
    matter = models.ForeignKey(
        'Matter',
        related_name='invoices',
        on_delete=models.SET_NULL,
        null=True,
    )
    billing_items = models.ManyToManyField(
        'BillingItem',
        verbose_name=_('billing_items'),
        related_name='billing_items_invoices'
    )
    period_start = models.DateField(
        verbose_name=_('Period start'),
        help_text=_(
            'Start date from which invoice money amount is calculated'
        ),
    )
    period_end = models.DateField(
        verbose_name=_('Period end'),
        help_text=_('End date till which invoice money amount is calculated')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title which describes current invoice')
    )

    INVOICE_STATUS_OVERDUE = 'overdue'
    INVOICE_STATUS_OPEN = 'open'
    INVOICE_STATUS_PAID = 'paid'
    INVOICE_STATUS_VOIDED = 'voided'
    INVOICE_STATUS_DRAFT = 'draft'

    AVAILABLE_FOR_EDITING_STATUSES = (
        AbstractPaidObject.PAYMENT_STATUS_NOT_STARTED,
    )
    FORBID_EDITING = (
        AbstractPaidObject.PAYMENT_STATUS_IN_PROGRESS,
        AbstractPaidObject.PAYMENT_STATUS_FAILED,
        AbstractPaidObject.PAYMENT_STATUS_PAID,
    )

    INVOICE_STATUSES = (
        (INVOICE_STATUS_OVERDUE, _('Overdue')),
        (INVOICE_STATUS_OPEN, _('Open')),
        (INVOICE_STATUS_PAID, _('Paid')),
        (INVOICE_STATUS_VOIDED, _('Voided')),
        (INVOICE_STATUS_DRAFT, _('Draft')),
    )

    status = FSMField(
        max_length=30,
        choices=INVOICE_STATUSES,
        default=INVOICE_STATUS_DRAFT,
        verbose_name=_('Status'),
        help_text=_('Status of invoice')
    )

    payment_method = models.ManyToManyField(
        PaymentMethods,
        verbose_name=_('Payment methods'),
        related_name='invoices'
    )

    note = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('A note left by mediator')
    )

    created_by = models.ForeignKey(
        to=AppUser,
        #editable=False,
        verbose_name=_('Created by'),
        help_text=_('AppUser that created invoice'),
        related_name='invoices',
        on_delete=models.PROTECT,
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_(
            "The date on which payment for this invoice is due."
        ),
        verbose_name='Due Date'
    )
    due_days = models.IntegerField(
        default=0,
        help_text=_(
            "The days on which payment for this invoice is due."
        ),
        verbose_name='Due days'
    )
    email = models.EmailField(
        verbose_name=_('Invoice Email'),
        null=True,
    )
    finalized = models.DateTimeField(
        verbose_name=_('Finalized Date'),
        null=True,
        blank=True
    )

    activities = models.ManyToManyField(
        'InvoiceActivity',
        verbose_name=_('activities'),
        related_name='invoices',
    )

    logs = models.ManyToManyField(
        'InvoiceLog',
        verbose_name=_('logs'),
        related_name='invoices',
    )

    # tax
    tax_rate = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        verbose_name=_('Tax rate'),
        help_text=_('Tax rate'),
        null=True,
        default=None
    )

    objects = InvoiceQuerySet.as_manager()

    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')

    def __str__(self):
        return self.title

    @property
    def total_amount(self) -> Decimal:
        amount = 0
        for item in self.billing_items.all():
            if item.is_billable:
                amount += float(item.fee)
        return round(decimal.Decimal(amount) * (
                1 + (self.tax_rate or 0) / decimal.Decimal(100)), 2)

    @property
    def time_billed(self) -> timedelta:
        """ Возвращает сумму затраченных времени на выполнение заданий. """
        time_billed = timedelta()
        for obj in self.billing_items.all():
            if obj.time_spent:
                time_billed += obj.time_spent
        return time_billed

    @property
    def fees_earned(self) -> float:
        """ Возвращает сумму гонораров за работу. """
        fees = sum(
            [obj.fee for obj in self.billing_items.all() if obj.is_billable])
        return fees

    @property
    def can_be_paid(self) -> bool:
        """ Проверьте, возможно ли оплатить счет. """
        deposit_account = self.matter.mediator.deposit_account
        return bool(
            self.fees_earned > 0 and
            deposit_account and
            deposit_account.is_verified and
            self.status == self.INVOICE_STATUS_OPEN
        )

    @property
    def available_for_editing(self) -> bool:
        """ Счет-фактуру можно редактировать? """
        return self.payment_status in self.AVAILABLE_FOR_EDITING_STATUSES

    def can_send(self, user) -> bool:
        """ Возвращаем ``True`` если ``user`` может отправить счет-фактуру.
        Счет-фактура может быть отправлен только оригиналом счета-фактуры "поверенный`
        или пользователи, которым был предоставлен доступ к этому вопросу. Исключение 
        составляют статусы связанные с платежами и если в счете-фактуре нет временных 
        накладных. Счет-фактура может быть отправлен только в том случае, если статус 
        оплаты указан в "not_started".
        """
        if not user:
            return False

        if self.payment_status != self.PAYMENT_STATUS_NOT_STARTED:
            raise ValidationError(dict(
                payment_status='Invoice is being paid or is already paid'
            ))

        if not self.time_billing.exists():
            raise ValidationError(dict(
                fees_earned="Invoice doesn't have any time billings"
            ))

        matter = self.matter
        return user.pk == matter.mediator_id or matter.is_shared_for_user(
            user
        )

    def can_pay(self, user) -> bool:
        """Возвращаем ``True`` если ``user`` может оплатите счет.

        Счет может быть оплачен только клиентом. Также счет-фактура может быть оплачен, если 
        сборы больше нуля (Stripe не позволит нам создать платежное намерение с помощью
        сумма, равная нулю). Это не может быть использовано для "ожидающих" или "отправленных"
        переходы, поскольку они обрабатываются параметрами источников fcm. Также для оплаты
        нам нужен адвокат по вопросам выставления счетов, чтобы иметь учетную запись в Stripe
        Connect.
        """
        if not super().can_pay(user):
            return False
        return user.pk == self.matter.client_id and self.can_be_paid

    @transition(
        field=status,
        source=INVOICE_STATUS_DRAFT,
        target=INVOICE_STATUS_OPEN,
        permission=can_send,
    )
    def send(self, user=None):
        """ Обновите статус счета-фактуры до `открыт`.
        Обновите статус счета на `открыт` и отправьте электронное письмо со счетом указанному
        клиенту.
        """
        from .. import services
        from ..signals import invoice_is_created
        try:
            invoice = stripe.Invoice.send_invoice(
                self.invoice_id
            )
            services.send_invoice(invoice=self, stripe_invoice=invoice)
            self.finalized = timezone.now()
            self.save()
            invoice_is_created.send(
                sender=Invoice,
                instance=self
            )
        except Exception as error:
            logger.error(
                f'Error invoice #{self.pk} PDF sending: {error}\n'
                'Traceback:\n'
                f'{traceback.format_exc()}'
            )
            raise TransitionFailedException(str(error))

    @transition(
        field=status,
        source=[INVOICE_STATUS_OPEN, INVOICE_STATUS_OVERDUE],
        target=INVOICE_STATUS_PAID,
    )
    def pay(self):
        from .. import services
        try:
            invoice = stripe.Invoice.pay(self.invoice_id)
            services.pay_invoice(invoice=self, stripe_invoice=invoice)
        except Exception as error:
            logger.error(
                f'Error invoice #{self.pk} Paid: {error}\n'
                'Traceback:\n'
                f'{traceback.format_exc()}'
            )
            raise TransitionFailedException('Can not pay invoice')

    def _get_or_create_payment(self):
        """ Настройте оплату. """
        from ..services import get_or_create_invoice_payment
        return get_or_create_invoice_payment(invoice=self)

    def _post_start_payment_process_hook(self):
        """ Очистите другие счета-фактуры. """
        from ..services import prepare_invoice_for_payment
        prepare_invoice_for_payment(invoice=self)

    def _post_fail_payment_hook(self):
        """ Уведомить пользователя о несостоявшемся платеже. """
        from .. import notifications
        notifications.InvoicePaymentFailedNotification(paid_object=self).send()

    def _post_cancel_payment_hook(self):
        """ Уведомить пользователя об отмененном платеже. """
        from .. import notifications
        notifications.InvoicePaymentCanceledNotification(
            paid_object=self
        ).send()

    def _post_finalize_payment_hook(self):
        """ Уведомите клиента и адвоката об успешной оплате. """
        from .. import notifications
        for recipient in [self.matter.client, self.matter.mediator]:
            notifications.InvoicePaymentSucceededNotification(
                paid_object=self,
                recipient=recipient.user
            ).send()

    # def clean_matter(self):
    #     """ Счета-фактуры могут быть созданы для товаров с типом тарифа `почасовая`. """
    #     if not self.matter.is_hourly_rated:
    #         raise ValidationError(_(
    #             "Forbidden to add invoices to not `hourly` rated matters"
    #         ))

    @classmethod
    def client_upcoming_invoices(cls, client):
        return cls.objects.filter(
            matter__in=client.matters.all()
        ).filter(
            status__in=[cls.INVOICE_STATUS_OPEN, cls.INVOICE_STATUS_OVERDUE]
        )
