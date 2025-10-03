import uuid
from abc import abstractmethod

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

import stripe
from django_fsm import FSMField, transition
from djstripe.enums import PaymentIntentStatus
from djstripe.models import PaymentIntent
from stripe.error import StripeError
from apps.users.models.users import AppUser
from libs.django_fcm.exceptions import TransitionFailedException

from ....core.models import BaseModel
from .querysets import AbstractPaidObjectQuerySet


class Payment(BaseModel):
    """Base payment object to track different users payment across app.

    Attributes:
        payer (AppUser): The one who makes payment
        recipient (AppUser): The one who gets payment
        payment_content_type (ContentType):
            type of payment content related to payment itself
            (For now it can be PaymentIntentProxy object from djstripe)
        payment_object_id (int): id of payment content object
        payment_content_object (AbstractPaymentObject):
            Link to an payment object, used to track payment in service where
            payment was made. In case of stripe, we use it to find related
            payment on webhook event.
        amount (Decimal): Amount of money that would be paid in USD
        application_fee_amount (Decimal): Amount of money that would be taken
            from amount to the owner of app
        description (str): Description of payment
        status (str): Status of payment:
            - in_progress -> Payment is currently in progress(
                can be failed, canceled or finished)
            - failed -> Indicates last attempt failed(can be failed, canceled
            or finished), it still can succeeded, because client can change
            payment method outside backends reach.
            - canceled -> Payment was canceled from stripe dashboard or by
            payer(can't be changed, payment will de-attached for paid object)
            - succeeded -> Payment was succeeded(can't be changed)
        idempotency_key (UUID): Idempotency key,
            used to avoid creating duplicated data in payment services

    """
    payer = models.ForeignKey(
        to=AppUser,
        on_delete=models.PROTECT,
        related_name='made_payments',
        verbose_name=_('Payer'),
        help_text=_('Link to the user who made payment')
    )
    recipient = models.ForeignKey(
        to=AppUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('Recipient'),
        help_text=_('Link to the user to whom payment was made')
    )

    payment_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT
    )
    payment_object_id = models.PositiveIntegerField(
        db_index=True
    )
    payment_content_object = GenericForeignKey(
        ct_field='payment_content_type',
        fk_field='payment_object_id',
        for_concrete_model=False,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Amount'),
        help_text=_('Amount of money that would be paid in USD'),
    )
    application_fee_amount = models.DecimalField(
        default=0.0,
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Application fee amount'),
        help_text=_(
            'Amount of money that would be taken from amount '
            'to the owner of app'
        ),
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Description of payment')
    )

    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_FAILED = 'failed'
    STATUS_CANCELED = 'canceled'
    STATUS_SUCCEEDED = 'succeeded'

    STATUSES = (
        (STATUS_IN_PROGRESS, _('In progress')),
        (STATUS_FAILED, _('Failed')),
        (STATUS_CANCELED, _('Canceled')),
        (STATUS_SUCCEEDED, _('Succeeded')),
    )

    status = FSMField(
        max_length=30,
        choices=STATUSES,
        default=STATUS_IN_PROGRESS,
        verbose_name=_('Status'),
        help_text=_('Status of payment')
    )

    idempotency_key = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        verbose_name=_('Idempotency key'),
        help_text=_('Idempotency key, used to avoid creating duplicated data')
    )

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        unique_together = ('payment_content_type', 'payment_object_id')

    def __str__(self):
        return f'Payment #{self.pk} from {self.payer}'

    @property
    def paid_object(self):
        """Get object that was or being paid for."""
        if hasattr(self, 'invoice'):
            return self.invoice
        if hasattr(self, 'support'):
            return self.support
        return None

    @property
    def payment_object_data(self) -> dict:
        """Prepare payment data to return it in API."""
        return dict(
            client_secret=self.payment_content_object.client_secret,
            status=self.payment_content_object.status,
        )

    @transition(
        field=status,
        source=[
            STATUS_IN_PROGRESS,
            STATUS_FAILED,
        ],
        target=STATUS_IN_PROGRESS,
    )
    def start_payment_process(self):
        """Mark payment as in progress"""

    @transition(
        field=status,
        source=[
            STATUS_IN_PROGRESS,
            STATUS_FAILED,
        ],
        target=STATUS_FAILED,
    )
    def fail_payment(self):
        """Fail payment."""
        self._update_paid_object(object_transition='fail_payment')

    @transition(
        field=status,
        source=[
            STATUS_IN_PROGRESS,
            STATUS_FAILED,
        ],
        target=STATUS_CANCELED,
    )
    def cancel_payment(self):
        """Cancel payment."""
        try:
            self.payment_content_object.cancel()
        except StripeError as e:
            raise TransitionFailedException(e)

        self._update_paid_object(object_transition='cancel_payment')

    @transition(
        field=status,
        source=[
            STATUS_IN_PROGRESS,
            STATUS_FAILED,
        ],
        target=STATUS_SUCCEEDED,
    )
    def finalize_payment(self):
        """Finalize payment."""
        self._update_paid_object(object_transition='finalize_payment')

    def _update_paid_object(self, object_transition: str):
        """Preform transition for paid object."""
        paid_object = self.paid_object
        # No linked paid object, skipping.
        if not paid_object:
            return
        getattr(paid_object, object_transition)()
        paid_object.save()


class AbstractPaymentObject(models.Model):
    """Abstract payment object.

    This should be used on models that we'll be set as payment_content_object
    in Payment model.

    """

    class Meta:
        abstract = True

    @abstractmethod
    def cancel(self):
        """Cancel payment."""

    @property
    def payment(self) -> Payment:
        """Get payment for payment object."""
        content_type = ContentType.objects.get_for_model(
            self, for_concrete_model=False,
        )
        return Payment.objects.filter(
            payment_content_type=content_type, payment_object_id=self.pk
        ).first()


class PaymentIntentProxy(PaymentIntent, AbstractPaymentObject):
    """Proxy for `PaymentIntent` djstripe model.

    It adds useful methods related to Stripe API to work with payments.

    """

    class Meta:
        proxy = True

    def cancel(self):
        """Cancel payment intent."""
        stripe_payment = stripe.PaymentIntent.retrieve(id=self.id)
        if stripe_payment.status == PaymentIntentStatus.canceled:
            # Payment is already canceled, skipping
            return
        stripe_payment.cancel()


class AbstractPaidObject(models.Model):
    """Abstract paid payment object.

    This should be used on models that users can pay for(For example invoices
    or fee for support profile).

    Attributes:
        payment (Payment): Link to object's payment
        payment_status (str): Status of payment. Can be:
            * not_started - Payment is about to start or was canceled and
            will be restarted.
            * payment_in_progress - Fee payment is in progress
            * payment_failed - Fee payment attempt failed
            * paid - Fee paid

    """

    # Constants that can be used in status fields
    PAYMENT_STATUS_NOT_STARTED = 'not_started'
    PAYMENT_STATUS_IN_PROGRESS = 'payment_in_progress'
    PAYMENT_STATUS_FAILED = 'payment_failed'
    PAYMENT_STATUS_PAID = 'paid'

    PAYMENT_STATUSES = (
        (PAYMENT_STATUS_NOT_STARTED, _('Not started')),
        (PAYMENT_STATUS_IN_PROGRESS, _('Payment in progress')),
        (PAYMENT_STATUS_FAILED, _('Payment failed')),
        (PAYMENT_STATUS_PAID, _('Paid')),
    )

    payment_status = FSMField(
        max_length=30,
        choices=PAYMENT_STATUSES,
        default=PAYMENT_STATUS_NOT_STARTED,
        verbose_name=_('Payment Status'),
        help_text=_("Status of payment")
    )

    payment = models.OneToOneField(
        to='finance.Payment',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='%(class)s',
        related_query_name="%(app_label)s_%(class)s",
        verbose_name=_('Payment'),
        help_text=_('Link to payment')
    )

    objects = AbstractPaidObjectQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_paid(self) -> bool:
        """Shortcut to check whether user already paid for object."""
        return self.payment_status == self.PAYMENT_STATUS_PAID

    @property
    def is_in_progress(self) -> bool:
        """Shortcut to check whether user already started paying for object."""
        return self.payment_status == self.PAYMENT_STATUS_IN_PROGRESS

    def can_pay(self, user) -> bool:
        """Return `True` if `user` can pay for object"""
        if not user:
            return False
        return True

    @abstractmethod
    def _get_or_create_payment(self) -> Payment:
        """Generate payment for object."""

    @transition(
        field=payment_status,
        source=[
            PAYMENT_STATUS_NOT_STARTED,
            PAYMENT_STATUS_IN_PROGRESS,
            PAYMENT_STATUS_FAILED,
        ],
        target=PAYMENT_STATUS_IN_PROGRESS,
        permission=lambda instance, user: instance.can_pay(user)
    )
    def start_payment_process(self, user=None) -> Payment:
        """Setup payment for Paid object."""
        try:
            self.payment = self._get_or_create_payment()
        except StripeError as error:
            raise TransitionFailedException(error.user_message)
        self._post_start_payment_process_hook()
        return self.payment

    @transition(
        field=payment_status,
        source=PAYMENT_STATUS_IN_PROGRESS,
        target=PAYMENT_STATUS_FAILED,
    )
    def fail_payment(self):
        """Inform user that it's payment has failed"""
        self._post_fail_payment_hook()

    @transition(
        field=payment_status,
        source=[
            PAYMENT_STATUS_IN_PROGRESS,
            PAYMENT_STATUS_FAILED,
        ],
        target=PAYMENT_STATUS_NOT_STARTED,
    )
    def cancel_payment(self, user=None):
        """Cancel payment and detach payment intent from paid object"""
        self.payment = None
        self._post_cancel_payment_hook()

    @transition(
        field=payment_status,
        source=[
            PAYMENT_STATUS_IN_PROGRESS,
            PAYMENT_STATUS_FAILED,
        ],
        target=PAYMENT_STATUS_PAID,
    )
    def finalize_payment(self):
        """Mark payment as paid and inform user about it."""
        self._post_finalize_payment_hook()

    def _post_start_payment_process_hook(self):
        """Perform action after `start_payment_process` transition."""

    def _post_fail_payment_hook(self):
        """Perform action after `fail_payment` transition."""

    def _post_cancel_payment_hook(self):
        """Perform action after `cancel_payment` transition."""

    def _post_finalize_payment_hook(self):
        """Perform action after `finalize_payment` transition."""
