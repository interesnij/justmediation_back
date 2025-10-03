from django.db.models import signals
from django.dispatch import Signal, receiver
from django.utils import timezone
from .. import models
from ..models import BillingItem, Invoice
from ..services import (
    attach_time_billings_to_invoice,
    get_invoice_for_matter,
    get_invoice_period_ranges,
)

invoice_is_sent = Signal(providing_args=('instance', 'user'))
invoice_is_sent.__doc__ = 'Signal which means that matter invoice was sent'

invoice_is_created = Signal(providing_args=('instance'))
invoice_is_created.__doc__ = 'Signal which means that matter invoice was sent'

billing_item_is_created = Signal(providing_args=('instance'))
billing_item_is_created.__doc__ = 'Signal which means that item was created'


@receiver(signals.post_save, sender=BillingItem)
def update_time_entries(sender, instance, **kwargs):
    """
    Update the orphan time entries with newly created billing item.
    """

    models.TimeEntry.objects.filter(
        created_by=instance.created_by,
        billing_item__isnull=True
    ).update(billing_item=instance)


@receiver(signals.post_save, sender=Invoice)
def process_invoice_create_update(instance: Invoice, created: bool, **kwargs):
    """Attach time billings to invoice

    Whenever new invoice is created or dates are updated for already existing
    invoice, all existing within matter time billings with corresponding dates
    should be attached to it.

    We do nothing if invoice is not hourly rated, or is not available for
    editing.

    """
    # do nothing if instance matter is not hourly rated
    if not instance.matter.is_hourly_rated:
        return

    # do nothing if instance is already have been paid
    if not instance.available_for_editing:
        return

    is_period_changed = (
        'period_start' in instance.get_dirty_fields() or
        'period_end' in instance.get_dirty_fields()
    )
    if not created and not is_period_changed:
        return

    # prepare time billings for which links should be created
    matched = BillingItem.objects.filter(
        matter=instance.matter
    ).match_period(
        period_start=instance.period_start,
        period_end=instance.period_end
    ).available_for_editing().values_list('id', flat=True)
    existing = instance.attached_time_billing.values_list(
        'time_billing', flat=True
    )
    attach_time_billings_to_invoice(matched, existing, instance)


@receiver(signals.post_save, sender=BillingItem)
def process_time_billing_create_update(sender, instance, created, **kwargs):
    """Attach time billing to invoice.

    Whenever new time billing is created or its date is updated - it is needed
    to make TB and Invoice reattachments.

    Steps:

        1. Try to find matching to time billing `date` invoices within a matter

        2. If no matching invoices exists and date is for a current month of a
        current year -> do nothing and wait until celery task will generate it
        automatically

        3. If no matching invoices exists and date is for a `past` period ->
        generate new invoice and attach time billing to it.

        4. If there are existing matching invoices -> attach current time
        billing to matching invoices and detach from not matching ones anymore

    Do nothing if time billing's matter is not `hourly` rated or not `date`
    field is updated or if time billing's invoice is not available for editing.

    """
    if instance.matter:
        billing_item_is_created.send(
            sender=models.BillingItem,
            instance=instance
        )
    # do nothing if instance matter is not hourly rated
    if not instance.matter.is_hourly_rated:
        return

    # do nothing if time_billing is not available for editing
    if not instance.available_for_editing:
        return

    # do nothing if not instance `date` field is updated
    if not created and 'date' not in instance.get_dirty_fields():
        return

    # find invoices with matching period
    date = instance.date
    matched = instance.matter.invoices.available_for_editing().match_date(
        date=date
    ).values_list('id', flat=True)

    # if there are no matching invoices and current datetime month and year are
    # the same as time billing `date`month and year -> do nothing cause
    # invoice will be auto generated at the 1st day of a next month by app
    now = timezone.now().date()
    is_actual_date = now.month == date.month and now.year == date.year
    if not matched.exists() and is_actual_date:
        # delete current TB attachments to not matching anymore invoices
        instance.attached_invoice.all().delete()
        return
    # if no related invoice exists for a past date - generate a new one
    # according to time billing date (get first day of a `date` month and last
    # day of `date` month)
    elif not matched.exists() and not is_actual_date:
        period_start, period_end = get_invoice_period_ranges(date)
        # delete current TB attachments to not matching anymore invoices
        instance.attached_invoice.all().delete()
        # during invoice creation time billing will be attached
        get_invoice_for_matter(instance.matter, period_start, period_end)
        return

    # otherwise - we assume that time billing should be attached to invoices
    existing = instance.invoices.values_list('id', flat=True)
    attach_time_billings_to_invoice(matched, existing, instance)


@receiver(signals.pre_save, sender=BillingItem)
def set_created_by(instance: BillingItem, **kwargs):
    """Set `created_by` for time billing as matter's Mediator if it is not set.
    """
    if not instance._state.adding or hasattr(instance, 'created_by'):
        return

    instance.created_by = instance.matter.mediator.user
