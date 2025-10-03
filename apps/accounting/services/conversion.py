from datetime import date
from quickbooks import objects as qb_objects
from libs.quickbooks.services import create_qb_object
from apps.business.models import BillingItemAttachment, Invoice
from apps.users.models.clients import Client


def invoice_to_qb_object(
    invoice: Invoice, qb_customer: qb_objects.Customer
) -> qb_objects.Invoice:
    """Ярлык для преобразования "счета-фактуры` в соответствующий объект QB Invoice.
    Выполните сопоставление полей, чтобы перевести счета-фактуры приложения в формат QB Invoices.
    В настоящее время счет-фактура приложения представлена в виде простого QB-счета с несколькими
    Объекты `Строка товара для продажи" с информацией.
    Аргументы:
        счет-фактура (Invoice): экземпляр счета-фактуры приложения, который следует экспортировать в QB
        qb_customer (qb_objects.Клиент): Объект клиента QB, к которому относится счет-фактура
            прикрепленный

    """
    qb_obj = create_qb_object(
        qb_class=qb_objects.Invoice,
        CustomerRef=qb_customer.to_ref(),
        BillEmail=qb_customer.PrimaryEmailAddr
    )

    # добавить строку общего описания для счета-фактуры
    description = (
        f'Matter: #{invoice.matter.code} - {invoice.matter.title}\n\n'
        f'Invoice: {invoice.title}\n'
        f'({_format_date(invoice.period_start)} - '
        f'{_format_date(invoice.period_end)})\n\n'
    )
    qb_obj.Line.append(
        create_qb_object(
            qb_class=qb_objects.DescriptionOnlyLine,
            Description=description,
        )
    )

    # подготовьте описание счета-фактуры из элементов выставления счетов
    attachments = BillingItemAttachment.objects.filter(invoice=invoice) \
        .order_by('time_billing__date')
    for num, attachment in enumerate(attachments, start=1):
        qb_line = time_billing_attachment_to_qb_object(attachment, num)
        qb_obj.Line.append(qb_line)

    return qb_obj


def time_billing_attachment_to_qb_object(
    attachment: BillingItemAttachment, line_num: int = 0
) -> qb_objects.SalesItemLine:
    """Ярлык для преобразования `Вложения платежной позиции` в объект строки счета QB.
    Аргументы:
        вложение (Вложение элемента выставления счета): appt TBA экземпляр некоторого счета-фактуры
        line_num (int): номер строки, под которым TBA добавлен в счет QB
    """
    tb = attachment.time_billing
    description = (
        f'Job description: {tb.description}\n'
        f'Time spent: {tb.time_spent}\n'
    )

    return create_qb_object(
        qb_class=qb_objects.SalesItemLine,
        LineNum=line_num,
        Amount=tb.fees,
        Description=description,
        SalesItemLineDetail=create_qb_object(
            qb_class=qb_objects.SalesItemLineDetail,
            ServiceDate=_format_date(tb.date)
        )
    )


def client_to_qb_object(client: Client) -> qb_objects.Customer:
    """Ярлык для преобразования `Client` в соответствующий объект QB Customer.
    Аргументы:
        клиент (Client): экземпляр клиента приложения, преобразованный в QB Customer
    """
    return create_qb_object(
        qb_class=qb_objects.Customer,
        GivenName=client.user.first_name,
        FamilyName=client.user.last_name,
        DisplayName=client.display_name,
        CompanyName=client.organization_name,
        PrimaryEmailAddr=create_qb_object(
            qb_class=qb_objects.EmailAddress,
            Address=client.email
        ),
    )


def _format_date(obj: date):
    """Ярлык для форматирования даты в соответствующем для QB формате данных."""
    return date.strftime(obj, '%Y-%m-%d')
