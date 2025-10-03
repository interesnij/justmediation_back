from quickbooks import objects as qb_objects
from libs.quickbooks import exceptions
from libs.quickbooks.clients import QuickBooksClient
from apps.business.models import Invoice
from apps.users.models import AppUser
from apps.users.models.clients import Client
from ..models import QBInvoice
from .conversion import client_to_qb_object, invoice_to_qb_object


def sync_invoice(
    invoice: Invoice,
    qb_invoice: qb_objects.Invoice,
    qb_customer: qb_objects.Customer,
    qb_company_id: str,
    user: AppUser
):
    """Синхронизируйте созданный/обновленный счет QB с "Счетом QB`.
    Сохраните информацию о том, что "счет-фактура" уже был экспортирован пользователем в какую-либо компанию.
    Аргументы:
        счет-фактура (Invoice): экземпляр счета-фактуры приложения, который был экспортирован в QB
        qb_invoice (qb_objects.Счет-фактура): Счет-фактура QB с обновленной информацией
        qb_customer (qb_objects.Клиент): Клиент QB с обновленной информацией
        qb_company_id (str): идентификатор компании (realmId), в которую был экспортирован счет-фактура
        пользователь (AppUser): экспорт счетов-фактур, инициированный пользователем
    """

    saved_invoice = get_export_record_for_invoice(
        invoice, qb_customer, qb_company_id, user
    )
    if saved_invoice:
        return saved_invoice

    return QBInvoice.objects.create(
        user=user,
        invoice=invoice,
        qb_company_id=qb_company_id,
        qb_invoice_id=qb_invoice.Id,
        qb_customer_id=qb_customer.Id,
    )


def get_export_record_for_invoice(
    invoice: Invoice,
    qb_customer: qb_objects.Customer,
    qb_company_id: str,
    user: AppUser
):
    """Ярлык для проверки того, был ли "счет-фактура` уже экспортирован.
    Проверьте, был ли счет-фактура уже экспортирован этим пользователем в тот же QB
    компания с тем же клиентом QB
    Аргументы:
        счет-фактура (Invoice): экземпляр счета-фактуры приложения, который был экспортирован в QB
        qb_customer (qb_objects.Клиент): Клиент QB с обновленной информацией
        qb_company_id (str): идентификатор компании (realmId), в которую был экспортирован счет-фактура
        пользователь (AppUser): экспорт счетов-фактур, инициированный пользователем
    """
    return invoice.qb_invoices.filter(
        user=user, qb_company_id=qb_company_id, qb_customer_id=qb_customer.Id
    ).first()


def create_customer(
    client: Client, qb_api_client: QuickBooksClient
) -> qb_objects.Customer:
    """Создайте QB-клиента из app Client.
    Аргументы:
        клиент (Client): клиент приложения, который должен быть создан
        qb_api_client (клиент QuickBooks): клиент для работы с QuickBooks API
    """
    qb_client = client_to_qb_object(client)
    try:
        return qb_api_client.save_object(qb_client)
    except exceptions.DuplicatedObjectError:
        raise exceptions.DuplicatedObjectError('The client already exist')


def create_or_update_invoice(
    invoice: Invoice,
    qb_customer: qb_objects.Customer,
    qb_api_client: QuickBooksClient
) -> qb_objects.Invoice:
    """Создайте QB-клиента из app Client.
    Аргументы:
        счет-фактура (Invoice): счет-фактура приложения, который следует создать или обновить
        qb_customer (qb_objects.Клиент): Объект клиента QB
        qb_api_client (клиент QuickBooks): клиент для работы с QuickBooks API
    """
    # подготовьте простой шаблон "счета-фактуры" в формате QB
    invoice_template = invoice_to_qb_object(invoice, qb_customer)

    # если счет-фактура уже экспортирована, получите ее QB `Id` и `syncToken` для обновления
    already_exported = get_export_record_for_invoice(
        invoice, qb_customer, qb_api_client.realm_id, qb_api_client.user
    )
    if already_exported:
        # если экспортированный QBInvoice действительно существует в QuickBooks, выполните его повторную синхронизацию, чтобы
        # получить фактический `syncToken`
        try:
            exported_qb_invoice = qb_api_client.get_invoice(
                already_exported.qb_invoice_id
            )
            invoice_template.Id = exported_qb_invoice.Id
            invoice_template.SyncToken = exported_qb_invoice.SyncToken
        # в противном случае, если экспортированный счет QB не существует в QuickBooks - удалить
        # это из модели счета-фактуры QB
        except exceptions.ObjectNotFound:
            already_exported.delete()

    # выполните реальный запрос на создание / обновление в QuickBooks API
    qb_invoice = qb_api_client.save_object(invoice_template)

    # запомнить созданный/обновленный счет-фактуру в QB Invoice
    sync_invoice(
        invoice=invoice,
        qb_invoice=qb_invoice,
        qb_customer=qb_customer,
        qb_company_id=str(qb_api_client.realm_id),
        user=qb_api_client.user
    )

    return qb_invoice
