from datetime import datetime, timedelta

import arrow

from apps.users.models import AppUser

from .. import models

__all__ = (
    'get_time_billing_for_time_period',
    'attach_time_billings_to_invoice',
)


def get_time_billing_for_time_period(
    user: AppUser, start: datetime, end: datetime, time_frame: str = 'month'
) -> dict:
    """Calculate sum of time billed for time period divided by time frame."""
    stats = []
    total_sum = 0
    start = arrow.get(start)
    end = arrow.get(end)
    for range_date in list(arrow.Arrow.range(time_frame, start, end)):
        # Calculate time billed for time frame
        time_billing = models.BillingItem.objects \
            .calculate_time_billing_for_period(
                user=user,
                start_date=range_date.floor(time_frame).datetime,
                end_date=range_date.ceil(time_frame).datetime,
            )
        # If there no time billed, set it to timedelta
        if not time_billing:
            time_billing = timedelta()
        total_sum += time_billing.total_seconds() // 60
        stats.append(
            {
                'date': range_date.datetime,
                'count': time_billing.total_seconds() // 60
            },
        )

    return {
        'total_sum': total_sum,
        'stats': stats,
    }


def attach_time_billings_to_invoice(
    matched: list, existing: list,
    instance: models.BillingItem or models.Invoice
):
    """Shortcut to attach matching time billings with invoices.

    Method makes deletion of not matching anymore invoices/time billings,
    adding new matching invoices/time billings, skipping already added matching
    attachments.

    """
    to_create = set(matched) - set(existing)
    to_delete = set(existing) - set(matched)

    is_invoice = isinstance(instance, models.Invoice)
    # create new time billing attachments
    models.BillingItemAttachment.objects.bulk_create(
        models.BillingItemAttachment(
            **{
                'time_billing_id' if is_invoice else 'invoice_id': item,
                'invoice' if is_invoice else 'time_billing': instance
            }
        ) for item in to_create
    )

    # delete not matching anymore attachments
    models.BillingItemAttachment.objects.filter(
        **{
            'time_billing__id__in' if is_invoice
            else 'invoice__id__in': to_delete
        }
    ).delete()
