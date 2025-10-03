from decimal import Decimal
from typing import Type, Union

import stripe
from constance import config

from .. import models


def create_payment(
    amount: Union[float, Decimal],
    description: str,
    payer_id: Union[int, Type[int]],
    recipient_id: Union[int, Type[int]] = None,
    application_fee_amount: Union[float, Decimal] = None,
):
    """Generate payment and payment content object."""
    if application_fee_amount is None:
        application_fee_amount = amount * config.APPLICATION_FEE / 100
    payment = models.Payment(
        amount=amount,
        application_fee_amount=application_fee_amount,
        description=description,
        payer_id=payer_id,
        recipient_id=recipient_id,
    )
    payment.payment_content_object = create_payment_intent_from_payment(
        payment=payment
    )
    payment.save()
    return payment


def create_payment_intent_from_payment(
    payment: models.Payment
) -> models.PaymentIntentProxy:
    """Generate payment intent from payment."""
    payment_intent_data = dict(
        amount=int(payment.amount * 100),
        currency='usd',
        confirmation_method='automatic',
        description=payment.description,
        idempotency_key=str(payment.idempotency_key),
    )
    if payment.application_fee_amount:
        payment_intent_data.update(
            application_fee_amount=int(
                payment.application_fee_amount * 100
            )
        )
    if payment.recipient:
        deposit_account = payment.recipient.deposit_account
        payment_intent_data.update(
            on_behalf_of=deposit_account.id,
            transfer_data=dict(
                destination=deposit_account.id,
            )
        )
    return models.PaymentIntentProxy.sync_from_stripe_data(
        stripe.PaymentIntent.create(**payment_intent_data)
    )
