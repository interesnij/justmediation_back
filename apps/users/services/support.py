from constance import config

from ...finance.models import Payment
from ...finance.services import create_payment
from .. import models


def get_or_create_support_fee_payment(support: models.Support) -> Payment:
    """Get or create fee payment for Support user access."""
    if support.payment:
        payment = support.payment
    else:
        payment = create_payment(
            amount=config.USER_FEE,
            application_fee_amount=0.0,
            description=f'Staff user access fee {support}',
            payer_id=support.pk,
        )
    payment.start_payment_process()
    payment.save()
    return payment
