import os
import pwd
from django.conf import settings
from django.core.management import BaseCommand, CommandParser
from django.urls import reverse_lazy
import arrow
import stripe
from stripe import WebhookEndpoint


class Command(BaseCommand):
    """ Интерфейс командной строки для создания конечных точек webhooks """
    help = """Script to create webhooks in Stripe Dashboard"""

    TYPE_SUBSCRIPTIONS = 'subscriptions'
    TYPE_DEPOSITS = 'deposits'

    # List of events sent by webhooks
    subscriptions_events = sorted([
        # Payment intents
        'payment_intent.amount_capturable_updated',
        'payment_intent.canceled',
        'payment_intent.created',
        'payment_intent.payment_failed',
        'payment_intent.processing',
        'payment_intent.succeeded',
        # Charges
        'charge.captured',
        'charge.dispute.closed',
        'charge.dispute.created',
        'charge.dispute.funds_reinstated',
        'charge.dispute.funds_withdrawn',
        'charge.dispute.updated',
        'charge.expired',
        'charge.failed',
        'charge.pending',
        'charge.refund.updated',
        'charge.refunded',
        'charge.succeeded',
        'charge.updated',
        # Checkouts
        'checkout.session.completed',
        # Coupons
        'coupon.created',
        'coupon.deleted',
        'coupon.updated',
        # Customers
        'customer.bank_account.created',
        'customer.bank_account.deleted',
        'customer.bank_account.updated',
        'customer.card.created',
        'customer.card.deleted',
        'customer.card.updated',
        'customer.created',
        'customer.deleted',
        'customer.discount.created',
        'customer.discount.deleted',
        'customer.discount.updated',
        'customer.source.created',
        'customer.source.deleted',
        'customer.source.expiring',
        'customer.source.updated',
        'customer.subscription.created',
        'customer.subscription.deleted',
        'customer.subscription.trial_will_end',
        'customer.subscription.updated',
        'customer.tax_id.created',
        'customer.tax_id.deleted',
        'customer.tax_id.updated',
        'customer.updated',
        # Invoices
        'invoice.created',
        'invoice.deleted',
        'invoice.finalized',
        'invoice.marked_uncollectible',
        'invoice.payment_action_required',
        'invoice.payment_failed',
        'invoice.payment_succeeded',
        'invoice.sent',
        'invoice.upcoming',
        'invoice.updated',
        'invoice.voided',
        # Plans
        'plan.created',
        'plan.deleted',
        'plan.updated',
        # Products
        'product.created',
        'product.deleted',
        'product.updated',
        # Subscription schedule
        'subscription_schedule.aborted',
        'subscription_schedule.canceled',
        'subscription_schedule.completed',
        'subscription_schedule.created',
        'subscription_schedule.expiring',
        'subscription_schedule.released',
        'subscription_schedule.updated',
    ])

    deposits_events = sorted([
        "account.updated",
        "capability.updated",
        "account.external_account.created",
        "account.external_account.deleted",
        "account.external_account.updated",
    ])

    def add_arguments(self, parser: CommandParser) -> None:
        """Add positional arguments."""

        parser.add_argument(
            '--type',
            type=str,
            help=(
                'Set a type of webhook, it can be `subscriptions` (for simple '
                '`account` webhook) and `deposits` (for `connect` webhook)'
            ),
            required=True,
            choices=(self.TYPE_SUBSCRIPTIONS, self.TYPE_DEPOSITS)
        )

        parser.add_argument(
            '--host',
            type=str,
            default=settings.BASE_URL,
            help='Set a host of webhook, default is set to settings `BASE_URL`'
        )

        parser.add_argument(
            '--stripe_version',
            type=str,
            default=settings.STRIPE_WEBHOOK_VERSION,
            help=(
                'Set a version of api for webhook, default is set to '
                'settings `STRIPE_WEBHOOK_VERSION`'
            )
        )

        username = pwd.getpwuid(os.getuid()).pw_name
        current_time = arrow.utcnow().format('DD MMMM HH:mm:ss')
        default_description = (
            f'Webhook created by {username} at {current_time}'
        )
        parser.add_argument(
            '--description',
            type=str,
            default=default_description,
            help=(
                'Write description for webhook, '
                f'Default is: {default_description}'
            )
        )

    def handle(
        self,
        type: str,
        host: str,
        stripe_version: str,
        description: str,
        *args,
        **options,
    ) -> None:
        """Create webhook in stripe dashboard."""
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        webhook_url = f"{host}{reverse_lazy('v1:stripe-webhook')}"

        # create webhook
        webhook: WebhookEndpoint = stripe.WebhookEndpoint.create(
            url=webhook_url,
            api_version=stripe_version,
            enabled_events=self.deposits_events if type == self.TYPE_DEPOSITS
            else self.subscriptions_events,
            description=description,
            connect=True if type == self.TYPE_DEPOSITS else False
        )
        self.stdout.write(
            f'{type.capitalize()} webhook created \n'
            f'Webhook secret: {webhook.secret}\n'
            f'Url: {webhook_url}\n'
            f'Version: {stripe_version}\n'
            f'Description: {description}\n'
        )
