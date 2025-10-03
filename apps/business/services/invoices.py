import typing
from collections import namedtuple
from datetime import date as dt_date
import arrow
from ...finance.models import Payment
from ...finance.services import create_payment
from ...users.models import AppUser
from .. import models
from ..notifications import InvoiceEmailNotification

InvoicePeriod = namedtuple('InvoicePeriod', ['period_start', 'period_end'])

__all__ = (
    'get_invoice_period_str_representation',
    'get_invoice_period_ranges',
    'get_invoice_for_matter',
    'send_invoice_to_recipients',
    'prepare_invoice_for_payment',
    'get_or_create_invoice_payment',
)


def get_invoice_period_str_representation(
    invoice: models.Invoice, date_format: str, equality_attr: str = None
) -> str:
    """ Ярлык для получения строкового представления периода выставления счета.

    Метод подготавливает представление строки периода выставления счета в `date_format`.
    Если планируется проверка на равенство некоторых атрибутов `start` и `end`
    -> не повторять значение (будет возвращено `Oct` вместо `Oct - Oct`)

    Аргументы:
        invoice  (Invoice) - экземпляр счета-фактуры
        date_format (datetime) - возвращаемый формат для отдельной даты
        equality_attr (str) - имя атрибута, который должен быть проверен по качеству

    Возвращается:
        (str) - строка периода выставления счета в желаемом формате
    """
    start, end = invoice.period_start, invoice.period_end
    if equality_attr:
        start_attr = getattr(start, equality_attr, None)
        end_attr = getattr(end, equality_attr, None)
        # возвращает только одну дату в случае похожих значений
        if start_attr == end_attr:
            return start.strftime(date_format)
    # срок возврата в случае разных значений
    return f'{start.strftime(date_format)} - {end.strftime(date_format)}'


def get_invoice_period_ranges(
    date: typing.Union[dt_date, arrow.Arrow]
) -> InvoicePeriod:
    """ Ярлык для получения диапазонов периодов выставления счета от определенной `даты`.
    Метод получает `данные" и вычисляет первый и последний дни месяца даты и
    возвращает их в формате "Периода выставления счета".

    Аргументы:
        date (date) - дата, до которой должны быть рассчитаны диапазоны счетов-фактур.

    Возвращается:
        ((Invoice Period) - вычисленные значения для счета "period_start` и
    `period_end`
    """
    if isinstance(date, dt_date):
        date = arrow.get(date)
    period_start, period_end = date.span('month')
    return InvoicePeriod(
        period_start=period_start.datetime,
        period_end=period_end.datetime
    )


def get_invoice_for_matter(
    matter: models.Matter, period_start: dt_date, period_end: dt_date
) -> models.Invoice:
    """ Ярлык для получения или создания счета-фактуры по товару за желаемый период.

    Метод проверяет, существует ли счет-фактура за желаемый период, и использует
    это, если он существует, в противном случае он создает новый счет-фактуру.

    Аргументы:
        matter (Matter) - вопрос, по которому должен быть сгенерирован счет-фактура
        period_start (date) - дата начала периода выставления счета
        period_end (date) - дата окончания периода выставления счета

    Возвращается:
        (Invoice) - созданный или полученный счет-фактура по какому-либо вопросу

    """
    # проверьте, существует ли счет-фактура за желаемый период по данному вопросу
    invoice = matter.invoices.filter(
        period_start=period_start, period_end=period_end
    ).first()
    if invoice:
        return invoice

    # создайте новый счет-фактуру, если он не существует
    invoice = models.Invoice.objects.create(
        matter=matter,
        created_by_id=matter.mediator_id,
        period_start=period_start,
        period_end=period_end,
        title=f'{matter.title} Invoice',
    )
    return invoice


def send_invoice_to_recipients(
    invoice: models.Invoice,
    recipient_list: typing.Sequence[str],
    note: str = None,
    user: AppUser = None
) -> bool:
    """ Отправьте получателям сгенерированный файл отчета в формате pdf из счета-фактуры. """
    from ..signals import invoice_is_sent

    email_context = {
        'note': note
    }
    email = InvoiceEmailNotification(
        recipient_list=recipient_list,
        invoice=invoice,
        **email_context
    )
    send_status = email.send()

    # отправить сигнал о том, что счет был отправлен
    if send_status:
        invoice_is_sent.send(
            sender=invoice._meta.model,
            instance=invoice,
            user=user
        )

    return send_status


def prepare_invoice_for_payment(invoice: models.Invoice):
    """ Подготовьте счет для оплаты через Stripe Connect.

    Перед оплатой по счету-фактуре нам необходимо удалить другие
    счета-фактуры из временной накладной, прикрепленной к входному счету-фактуре.

    """
    # Получать pks за все время выставления счетов из счета-фактуры
    time_billings_pks = invoice.time_billing.values_list('pk', flat=True)
    # Удалять вложения к другим счетам за время
    models.BillingItemAttachment.objects.exclude(invoice=invoice).filter(
        time_billing_id__in=time_billings_pks
    ).delete()


def get_or_create_invoice_payment(invoice: models.Invoice) -> Payment:
    """Get or create payment for Invoice."""
    if invoice.payment:
        payment = invoice.payment
    else:
        payment = create_payment(
            amount=invoice.fees_earned,
            description=f'Payment for Invoice #{invoice.pk}-{invoice.title}',
            payer_id=invoice.matter.client_id,
            recipient_id=invoice.matter.mediator_id,
        )
    payment.start_payment_process()
    payment.save()
    return payment


def create_invoice_item(invoice: models.Invoice, stripe_invoice_item):
    if stripe_invoice_item is not None:
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"An invoice item for ${invoice.total_amount}USD "
                          f"was created for {invoice.client.user.email}")
            )
        )
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log='/v1/invoiceitems'
            )
        )
    else:
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log='/v1/invoiceitems'
            )
        )
    invoice.save()


def create_draft_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is not None:
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity="A draft invoice was created"
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"{invoice.client.user.email}'s "
                          "invoice item was added to an invoice")
            )
        )
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log='/v1/invoices'
            )
        )
    else:
        invoice.logs.add(
            models.links.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log='/v1/invoices'
            )
        )
    invoice.save()


def send_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is None:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/send'
            )
        )
    else:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/send'
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"A draft invoice for ${invoice.total_amount}USD "
                          f"to {invoice.client.user.email} was finalized")
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"{invoice.client.user.email}'s "
                          f"for ${invoice.total_amount}USD invoice was sent")
            )
        )
    invoice.save()


def pay_invoice(invoice: models.Invoice, stripe_invoice):
    if stripe_invoice is None:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='400 BAD REQUEST',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/pay'
            )
        )
    else:
        invoice.logs.add(
            models.InvoiceLog.objects.create(
                status='200 OK',
                method='POST',
                log=f'/v1/invoices/{invoice.invoice_id}/pay'
            )
        )
        invoice.activities.add(
            models.InvoiceActivity.objects.create(
                activity=(f"A invoice for ${invoice.total_amount}USD "
                          f"to {invoice.client.user.email} was paid")
            )
        )
    invoice.save()


def clone_invoice(obj, attrs={}):

    clone = obj._meta.model.objects.get(pk=obj.pk)
    clone.pk = None
    for key, value in attrs.items():
        setattr(clone, key, value)
    clone.save()
    fields = clone._meta.get_fields()
    for field in fields:
        if not field.auto_created and field.many_to_many:
            for row in getattr(obj, field.name).all():
                getattr(clone, field.name).add(row)
        if field.auto_created and field.is_relation:
            if field.many_to_many:
                pass
            else:
                attrs = {
                    field.remote_field.name: clone
                }
                children = field.related_model.objects.filter(
                    **{field.remote_field.name: obj}
                )
                for child in children:
                    clone_invoice(child, attrs)
    return clone
