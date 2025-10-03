"""Overridden djstripe models for `direct deposits` workflow (stripe connect)

Some djstripe models have restricted functionality. For example there can be
absent useful methods like `create` (create instance with stripe API and in
django models) and etc.

"""
import logging

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _

import stripe
from djstripe import settings as djstripe_settings
from djstripe.context_managers import stripe_temporary_api_version
from djstripe.models import Account, Event, WebhookEventTrigger
from stripe import Account as StripeAccount

from apps.core.models import BaseModel

from ...constants import Capabilities

logger = logging.getLogger('stripe')

# Set global api key for operations, not supported by dj-stripe
stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

__all__ = (
    'WebhookEventTriggerProxy',
    'AccountProxy',
    'AccountProxyInfo',
)


class WebhookEventTriggerProxy(WebhookEventTrigger):
    """Proxy for `WebhookEventTrigger` djstripe model.

    It adds useful and absent methods related to Stripe API to work with
    connect API webhooks.

    """

    class Meta:
        proxy = True

    def validate(self, api_key=None):
        """Overridden method which uses own webhook secret for connect API.

        So simple stripe webhooks use `WEBHOOK_SECRET` value and stripe connect
        webhooks use `DJSTRIPE_CONNECT_WEBHOOK_SECRET` from app settings. All
        of it is made because `djstripe` has almost no support for work with
        connect API.

        """
        local_data = self.json_body
        is_connect_api_webhook = 'account' in local_data
        if "id" not in local_data or "livemode" not in local_data:
            return False

        if self.is_test_event:
            logger.info("Test webhook received: {}".format(local_data))
            return False

        # choose proper secret depending on event
        webhook_secret = settings.DJSTRIPE_CONNECT_WEBHOOK_SECRET \
            if is_connect_api_webhook else settings.DJSTRIPE_WEBHOOK_SECRET

        if djstripe_settings.WEBHOOK_VALIDATION is None:
            # validation disabled
            return True
        elif (djstripe_settings.WEBHOOK_VALIDATION == "verify_signature"
                and webhook_secret):
            try:
                stripe.WebhookSignature.verify_header(
                    self.body,
                    self.headers.get("stripe-signature"),
                    # the main change is here - usage of `webhook_secret`
                    webhook_secret,
                    djstripe_settings.WEBHOOK_TOLERANCE,
                )
            except stripe.error.SignatureVerificationError:
                return False
            else:
                return True

        livemode = local_data["livemode"]
        api_key = api_key or djstripe_settings.get_default_api_key(livemode)

        # Retrieve the event using the api_version specified in itself
        with stripe_temporary_api_version(
            local_data["api_version"], validate=False
        ):
            remote_data = Event.stripe_class.retrieve(
                id=local_data["id"], api_key=api_key
            )

        return local_data["data"] == remote_data["data"]


class AccountProxy(Account):
    """Proxy for `Account` djstripe model.

    It adds useful and absent methods related to Stripe API to work with
    accounts.

    """

    class Meta:
        proxy = True

    @property
    def is_verified(self) -> bool:
        """Check whether current account verified by stripe or not.

        Account considered as verified if:
            - its `charges` and `payouts` are enabled
            - it has empty `requirements['eventually_due]`
            - all default requested by app `capabilities` are active

        https://stripe.com/docs/connect/identity-verification-api#
        determining-if-identity-or-business-verification-is-needed

        """
        if not (self.charges_enabled and self.payouts_enabled):
            return False

        if self.has_issues:
            return False

        if not hasattr(self, 'info') or not self.info.validate_capabilities():
            return False

        return True

    @property
    def has_issues(self) -> bool:
        """Check whether current account has errors in added data.

        https://stripe.com/docs/connect/identity-verification-api#
        determining-if-identity-or-business-verification-is-needed

        """
        return bool(self.requirements.get('eventually_due'))

    @property
    def login_url(self) -> str:
        """Method to get a link to connected account dashboard.

        Stripe docs: https://stripe.com/docs/connect/express-dashboard

        Returns:
            (str): link to express account dashboard

        """
        data = StripeAccount.create_login_link(self.id)
        return data.get('url')

    @classmethod
    def resync(cls, account_id):
        """Shortcut to resync account info from Stripe."""
        data = cls(id=account_id).api_retrieve()
        return cls.sync_from_stripe_data(data)

    @classmethod
    def sync_from_stripe_data(cls, data):
        """Overridden method to remember extra info in AccountProxyInfo.

        Because currently `djstripe` has almost no support for stripe connect
        features, we need to remember some absent in `Account` model fields:

            - capabilities - dict with statuses of requested by app
                capabilities (for verification process)
            - external_accounts - dict with connected to account
                `bank accounts` or `debit cards` (to display main user account
                in app)

        """
        instance = super().sync_from_stripe_data(data)
        instance_info, created = AccountProxyInfo.objects.get_or_create(
            account=instance
        )
        instance_info.external_accounts = data.get('external_accounts')

        # set capabilities only on new `info` object creation, cause later
        # their changes are tracked via `capability.updated` webhook
        if created:
            instance_info.capabilities = data.get('capabilities')

        instance_info.save()
        return instance

    def notify_user(self):
        """Shortcut to notify user whether his account is verified or not.
        """
        finance_profile = getattr(self, 'finance_profile', None)
        if not finance_profile:
            return

        if self.is_verified:
            logger.info(f'Initiate send of verified email for {self.id}')
            finance_profile.send_verified_email()
        elif self.has_issues:
            logger.info(f'Initiate send of not verified email for {self.id}')
            finance_profile.send_not_verified_email()


class AccountProxyInfo(BaseModel):
    """Separate model to store extra AccountProxy model info.

    This model adds absent in original `AccountProxy` and djstripe `Account`
    model fields.

    Attributes:
         account (AccountProxy): link to stripe connected Account
         capabilities (AccountProxy): link to stripe Account
         external_accounts (AccountProxy): link to stripe Account

    """
    account = models.OneToOneField(
        to='finance.AccountProxy',
        verbose_name=_('Current connected account'),
        on_delete=models.SET_NULL,
        related_name='info',
        null=True,
        blank=True,
        help_text=_('Represents related to stripe account for direct deposits')
    )
    capabilities = JSONField(
        verbose_name=_('Capabilities'),
        help_text=_(
            'Represents privileges for app provided by user to connected '
            'account'
        ),
        default=dict
    )
    external_accounts = JSONField(
        verbose_name=_('External accounts'),
        help_text=_("Represents payouts info of user's connected account"),
        default=list
    )

    class Meta:
        verbose_name = _('Account Proxy Info')
        verbose_name_plural = _('Accounts Proxies Info')

    def __str__(self):
        return f'Account Proxy Info: {self.account}'

    def validate_capabilities(self) -> bool:
        """Check whether capabilities are valid.

        Method considers capabilities as valid if all `Capabilities.default`
        are defined as `active`.

        https://stripe.com/docs/api/accounts/object#account_object-capabilities

        """
        for capability in Capabilities.default:
            value = self.capabilities.get(capability)
            if value != 'active':
                return False
        return True
