from typing import Sequence

from libs.notifications import email
from libs.utils import get_base_url

from ..business import models
from ..finance.notifications import BasePaymentNotification

__all__ = (
    'InvoiceEmailNotification',
    'InvoicePaymentSucceededNotification',
    'InvoicePaymentFailedNotification',
    'InvoicePaymentCanceledNotification',
)


class InvoiceEmailNotification(email.DefaultEmailNotification):
    """Used to send invoice's pdf file to clients."""
    template = 'business/email/invoice_notification.html'

    def __init__(
        self,
        recipient_list: Sequence[str],
        invoice: models.Invoice,
        **template_context
    ):
        """Init InvoiceEmailNotification."""
        super().__init__(
            recipient_list=recipient_list,
            **template_context,
        )
        self.invoice = invoice

    @property
    def deep_link(self) -> str:
        """Get frontend deep link."""
        return f'{get_base_url()}invoices/{self.invoice.id}'

    def get_subject(self):
        """Get email subject for matter."""
        return (
            f'New invoice from {self.invoice.matter.mediator.full_name}'
        )

    def get_files(self):
        """Prepare invoice file for email."""

        # Escape import error
        from .export.invoices import InvoiceResource
        pdf_resource = InvoiceResource(instance=self.invoice)

        file = email.EmailFile(
            filename=pdf_resource.filename,
            content=pdf_resource.export(),
            mimetype=pdf_resource.mimetype,
        )
        return file,

    def get_template_context(self):
        """Add invoice to email context."""
        context = super().get_template_context()
        context['invoice'] = self.invoice
        context['deep_link'] = self.deep_link
        return context


class BaseInvoicePaymentNotification(BasePaymentNotification):
    """Used to send notifications about invoice payments."""
    paid_object_name = 'invoice'

    def get_recipient_list(self):
        """Get client's email."""
        return [self.paid_object.matter.client.email]

    @property
    def deep_link(self) -> str:
        """Get frontend deep link."""
        return f'{get_base_url()}/invoices/{self.paid_object.id}'


class InvoicePaymentSucceededNotification(BaseInvoicePaymentNotification):
    """Used to send notification payment for invoice succeeded."""
    template = 'business/email/invoice_payment_succeeded.html'

    def __init__(self, recipient, *args, **kwargs):
        """Remember recipient of notification."""
        self.recipient = recipient
        super().__init__(*args, **kwargs)

    def get_recipient_list(self):
        """Get recipient's email."""
        return [self.recipient.email]

    def get_subject(self):
        """Get email subject for notification."""
        return f'Payment for invoice {self.paid_object} paid'

    def get_template_context(self):
        """Extend template context with recipient."""
        context = super().get_template_context()
        context['recipient'] = self.recipient
        return context


class InvoicePaymentFailedNotification(BaseInvoicePaymentNotification):
    """Used to send notification that payment for invoice failed."""
    template = 'business/email/invoice_payment_failed.html'

    def get_subject(self):
        """Get email subject for notification."""
        return f'Payment for invoice {self.paid_object} failed'


class InvoicePaymentCanceledNotification(BaseInvoicePaymentNotification):
    """Used to send notification that payment for invoice canceled."""
    template = 'business/email/invoice_payment_canceled.html'

    def get_subject(self):
        """Get email subject for notification."""
        return f'Payment for invoice {self.paid_object} canceled'
