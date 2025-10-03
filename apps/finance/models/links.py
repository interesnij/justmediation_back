from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from ..notifications import (
    StripeAccountNotVerifiedEmailNotification,
    StripeAccountVerifiedEmailNotification,
)
from apps.users.models.users import AppUser


class FinanceProfile(BaseModel):
    """Model with payment info for user (subscriptions and direct deposits).

    Attributes:
        user (AppUser): Relation to AppUser
        initial_plan (PlanProxy): Relation to Plan of Subscription
        was_promo_period_provided (bool): Used to determine if promo time for
            the first subscription was already provided or not
        deposit_account (AccountProxy): connected stripe account for direct
            deposits
        not_verified_email_sent (datetime): datetime when last `account not
            verified` email was sent
        verified_email_sent (datetime): datetime when last `account verified`
            email was sent

    Separate datetime fields for connected account `verified` and `not
    verified` events is needed to prevent sending of too many emails, cause
    `account.updated` webhook may be triggered few times in an hour.

    """
    user = models.OneToOneField(
        AppUser,
        primary_key=True,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='finance_profile'
    )
    initial_plan = models.ForeignKey(
        'finance.PlanProxy',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        to_field='id'
    )
    was_promo_period_provided = models.BooleanField(
        verbose_name=_('Was promo period provided'),
        default=False
    )

    # Stripe Connect integration

    # interval which helps to check whether `not verified` email should be sent
    # again or not
    SEND_EMAIL_INTERVAL = timedelta(days=1)

    deposit_account = models.OneToOneField(
        to='finance.AccountProxy',
        verbose_name=_('Current deposit account'),
        on_delete=models.SET_NULL,
        related_name='finance_profile',
        null=True,
        blank=True,
        help_text=_('Represents related to stripe account for direct deposits')
    )
    not_verified_email_sent = models.DateTimeField(
        verbose_name=_('Not verified email sent datetime'),
        help_text=_(
            'Datetime when deposit account `not verified` email was sent for '
            'the last time'
        ),
        null=True,
        blank=True
    )
    verified_email_sent = models.DateTimeField(
        verbose_name=_('Verified email sent datetime'),
        help_text=_(
            'Datetime when deposit account `verified` email was sent for the '
            'last time'
        ),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Finance Profile')
        verbose_name_plural = _('Finance Profiles')

    def __str__(self):
        return f'Finance Profile: {self.user}'

    def send_verified_email(self):
        """Shortcut to send email when `deposit_account` becomes verified.

        If account status is `verified` and user wasn't informed that his
        account was verified - send `verified` email and update
        `not_verified_email_sent` field with `None`.

        """
        if not self.deposit_account.is_verified:
            return

        # send email only when account haven't been verified before
        if self.verified_email_sent:
            return

        email = StripeAccountVerifiedEmailNotification(
            stripe_account_url=self.deposit_account.login_url,
            recipients=[self.user.email]
        )
        is_sent = email.send()
        if is_sent:
            self.verified_email_sent = timezone.now()
            self.not_verified_email_sent = None
            self.save()

    def send_not_verified_email(self):
        """Shortcut to send email when `deposit_account` is not verified.

        If account status is `not verified` and the latest sent message is
        older then 1 day or absent - send `not verified` email and update
        `verified_email_sent` field with `None`.

        """
        if self.deposit_account.is_verified:
            return

        # send email that account haven't been verified only once a day
        last_sent = self.not_verified_email_sent
        sent_long_time_ago = last_sent and \
            last_sent < timezone.now() - FinanceProfile.SEND_EMAIL_INTERVAL
        if not last_sent or sent_long_time_ago:
            email = StripeAccountNotVerifiedEmailNotification(
                stripe_account_url=self.deposit_account.login_url,
                recipients=[self.user.email],
            )
            is_sent = email.send()
            if is_sent:
                self.not_verified_email_sent = timezone.now()
                self.verified_email_sent = None
                self.save()
