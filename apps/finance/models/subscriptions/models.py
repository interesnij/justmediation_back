"""Overridden djstripe models for subscriptions workflow.

Some djstripe models have restricted functionality. For example there can be
absent useful methods like `create` (create instance with stripe API and in
django models) and etc.

"""
import logging
import time
from datetime import datetime
from typing import Optional, Tuple

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

import stripe
from djstripe import settings as djstripe_settings
from djstripe.enums import SubscriptionStatus
from djstripe.models import Customer, Plan, Product, Subscription
from stripe.error import InvalidRequestError

from apps.finance import services
from apps.finance.constants import PlanTypes
from apps.finance.exceptions import PaymentProfileCreationError
from apps.finance.models.subscriptions.querysets import PlanProxyQuerySet
from apps.finance.services import calculate_promo_subscription_period

logger = logging.getLogger('stripe')

# Set global api key for operations, not supported by dj-stripe
stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY


class ProductProxy(Product):
    """Proxy for `Product` djstripe model.

    It adds useful and absent methods related to Stripe API to create
    product and etc.

    """

    class Meta:
        proxy = True

    @classmethod
    def get_or_create(cls, **kwargs):
        """ Get or create a Product."""
        try:
            return Product.objects.get(id=kwargs.get("id")), False
        except Product.DoesNotExist:
            return cls.create(**kwargs), True

    @classmethod
    def create(cls, **kwargs):
        """Class method to create new Product with stripe API."""
        stripe_product = cls._api_create(**kwargs)
        product = cls.sync_from_stripe_data(stripe_product)
        return product


class PlanProxy(Plan):
    """Proxy for `Plan` djstripe model.

    It overrides some base `Plan` class methods and fixes errors in it to
    satisfy Stripe API.

    """

    class Meta:
        proxy = True
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    objects = PlanProxyQuerySet.as_manager()

    @classmethod
    def get_or_create(cls, **kwargs):
        """Get or create a Plan.

        Fix error with `kwargs`, sometimes `id` can be absent in **kwargs.

        """
        try:
            return Plan.objects.get(id=kwargs.get("id")), False
        except Plan.DoesNotExist:
            return cls.create(**kwargs), True

    def purge(self, **kwargs):
        """Remove not valid plan objects from DB.

        This method can be useful in local debug and plans manipulations on
        server (if we need to clean up not existing in stripe plans from DB).

        """
        try:
            self._api_delete()
        except InvalidRequestError as exc:
            if "No such plan:" in str(exc):
                # The exception was thrown because the stripe customer was
                # already deleted on the stripe side, ignore the exception
                pass
            else:
                # The exception was raised for another reason, re-raise it
                raise
        return super().delete(**kwargs)

    def delete(self, **kwargs):
        """Delete stripe object via api and next step - instances of db"""
        return self.purge(**kwargs)

    @classmethod
    def check_is_premium(cls, plan: 'Plan') -> bool:
        """Return True if plan store as `premium`

        The method allows to process `Plan` objects (dj-stripe) and to
        avoid an additional call ORM for getting `PlanProxy` (such in webhook)
        """
        type_plan = plan.metadata.get('type', '')
        return type_plan == PlanTypes.PREMIUM

    @classmethod
    def create(cls, **kwargs):
        """Updated `create` plan method to remove redundant for API fields.

        Plan model contains some not needed for Stripe API fields, which
        become reasons of errors (`name`, `description` and etc fields).

        """
        plan_args = kwargs.copy()
        description = plan_args.pop('description', None)
        livemode = plan_args.pop('livemode', None)

        # remove all keys with empty string values (because of Stripe API)
        plan_args = {k: v for k, v in plan_args.items() if v != ''}
        plan = super().create(**plan_args)

        plan.name = plan_args.get('nickname')
        plan.description = description
        plan.livemode = livemode
        plan.save()

        return plan


class SubscriptionProxy(Subscription):
    """Proxy for `SubscriptionProxy` djstripe model.

    It overrides some base `Subscription` class methods and
    fixes issue in creation

    """

    class Meta:
        proxy = True
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    @classmethod
    def create(cls, customer_id: str, plan_id: str,
               trial_end: int = None,
               **kwargs) -> 'SubscriptionProxy':
        """Create a Stripe Subscription via stripe API and sync with db

        Args:
            customer_id: Customer stripe ID
            plan_id: Plan stripe ID
            trial_end: timestamp for starting paid period after trial
            if need
            kwargs (dict): additional data for creation stripe subscription

        More information:
            https://stripe.com/docs/api/subscriptions/create

        """
        try:
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"plan": plan_id}],
                # Important param for success invoice of 3d secure card
                off_session=True,
                trial_end=trial_end,
                **kwargs
            )
        except stripe.error.StripeError as e:
            logger.error(e)
            raise PaymentProfileCreationError(e.user_message)
        # Sync the Stripe API return data to the database,
        # this way we don't need to wait for a webhook-triggered sync
        return SubscriptionProxy.sync_from_stripe_data(
            stripe_subscription
        )

    def update(self, new_plan_id: str,
               trial_end: int = None) -> 'SubscriptionProxy':
        """Update a Stripe Subscription via stripe API and sync with db

        Args:
            new_plan_id: New plan stripe ID
            trial_end: timestamp for starting paid period after trial
            if need
            kwargs (dict): additional data for creation stripe subscription

        More information:
            https://stripe.com/docs/api/subscriptions/create

        """
        try:
            subscription = self.api_retrieve()
            items = [{
                'id': subscription['items']['data'][0].id,
                'plan': new_plan_id,
            }]

            stripe_subscription = stripe.Subscription.modify(
                self.id,
                items=items,
                cancel_at_period_end=False,
                trial_end=trial_end,
            )
        except stripe.error.StripeError as e:
            logger.error(e)
            raise PaymentProfileCreationError(e.user_message)
        # Sync the Stripe API return data to the database,
        # this way we don't need to wait for a webhook-triggered sync
        return SubscriptionProxy.sync_from_stripe_data(
            stripe_subscription
        )

    def fill_items_for_switch_plan(self, new_plan_id) -> list:
        """Generate items data for check next invoice"""
        subscription = self.api_retrieve()
        return [{
            'id':  subscription['items']['data'][0].id,
            'plan': new_plan_id,
        }]

    def switching_plan_immediately(
            self, new_plan_id: str,
    ) -> 'SubscriptionProxy':
        """Switches the mediator to another billing plan

        Related docs:
        https://stripe.com/docs/billing/subscriptions/upgrading-downgrading
        """
        try:
            items = self.fill_items_for_switch_plan(new_plan_id)

            stripe_subscription = stripe.Subscription.modify(
                self.id,
                items=items,
                cancel_at_period_end=False,
            )

            # create upcoming invoice only for active subscriptions
            # if self.is_active:
            #     customer = self.customer
            #     # mediator to immediately pay the price difference when
            #     # switching to a more expensive plan
            #     # on the same billing cycle
            #     # This invoice created pulls in all pending invoice items on
            #     # that customer, including prorations.
            #     stripe.Invoice.create(
            #         customer=customer.id,
            #         auto_advance=True,  # auto-finalize draft after ~1 hour
            #         subscription=stripe_subscription.id,
            #         description=(
            #             f'Upgrade subscription {self.id} '
            #             f'to plan {new_plan_id} for {customer}'
            #         ),
            #         default_payment_method=customer.default_payment_method.id
            #     )
        except stripe.error.StripeError as e:
            logger.error(f"Couldn't switching to new plan subscription: {e}")
            raise e
        return SubscriptionProxy.sync_from_stripe_data(
            stripe_subscription
        )

    def switching_plan_at_end(self, new_plan_id: str) -> 'SubscriptionProxy':
        """Change next subscription plan in end billing period

        For example, When a user downgrades to Standard, they will keep their
        Premium Subscription until the next billing date

        Set the current subscription to cancel at the end  of the current
        billing period and create a new one that will take effect on
        the date the current one ends.

        Update `AppUser.active_subscription` implement via webhook

        """
        canceled_current_subscription = self.cancel_subscription()
        start_paid_date = canceled_current_subscription.current_period_end

        if self.customer.subscriber.customer.next_subscription:
            # update next subscription
            return self.customer.subscriber.customer.next_subscription.update(
                new_plan_id=new_plan_id,
                trial_end=start_paid_date
            )
        else:
            # create next subscription
            return SubscriptionProxy.create(
                customer_id=self.customer.id,
                plan_id=new_plan_id,
                trial_end=start_paid_date
            )

    def calculate_proration_cost(self, new_plan_id) -> Tuple[int, datetime]:
        """Review the cost of a proration before changing the subscription

        In the returned invoice, the invoice items reflect the prorations
        created by an update

        https://stripe.com/docs/billing/subscriptions/prorations

        Important:
        The prorated amount is calculated down to the second by Stripe.

        """
        proration_date = int(time.time())
        try:
            items = self.fill_items_for_switch_plan(new_plan_id)
            invoice = stripe.Invoice.upcoming(
                customer=self.customer.id,
                subscription=self.id,
                subscription_items=items,
                subscription_proration_date=proration_date,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Couldn't calculate proration cost: {e}")
            raise e

        current_prorations = [
            i for i in invoice.lines.data if i.period.start == proration_date
        ]
        cost = sum([p.amount for p in current_prorations])
        return cost, datetime.fromtimestamp(proration_date)

    def set_promo_period_v1(self) -> 'Subscription':
        """Set a free promotion period at the end of the initial subscription

        TODO: this method can be removed when all v1 subscriptions will be
            expired. As `v1` subscriptions are considered subscriptions with
            False `was_promo_period_provided`.

        By business logic, the mediator have the first 18-month plan
        subscription (12m paid + 6 initial trial).

        When the first year of subscription ends, we add promo period before
        paying for next year

        So it is a workaround for emulating an 18-month subscription

        Related docs:
        https://stripe.com/docs/billing/subscriptions/billing-cycle#api-trials

        """
        promo_end = services.get_promo_period_timestamp(
            self.current_period_end
        )
        try:
            stripe_subscription = stripe.Subscription.modify(
                self.id,
                trial_end=promo_end,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Couldn't set promo` period to subscription: {e}")
            raise e
        return self.sync_from_stripe_data(
            stripe_subscription
        )

    def cancel_subscription(self, at_period_end=True) -> 'Subscription':
        """Cancels mediator subscription at the end of the current period

        For active and trial subscriptions, unsubscribe is provided via set
        `at_period_end` value to true. And the date of cancellation will be
        equal `current_period_end` (or `renewal_date`).

        Notes:
            The specific cancellation timestamp is stored in `cancel_at` of
            stripe object. Now dj-stripe does not support mapping this field in
            `Subscription` objects (it will fix in next release)

        """
        try:
            # no need to cancel this canceled subscription again
            if self.is_canceled:
                return self
            return self.cancel(at_period_end=at_period_end)
        except stripe.error.StripeError as e:
            logger.error(
                f"Couldn't cancel a subscription: {e}"
                f"{self.id} subscription for customer {self.customer.id}"
            )
            raise e

    def cancel(self, at_period_end=True):
        """Overridden subscription `cancel` method because of specific logic

        Currently app has few subscription types that should be cancelled:

            - trialing (should be cancelled at `period_end` without renewal)

            - active (should be cancelled at `period_end` without renewal)

            - active + trial - old type of subscriptions (should be cancelled
                after ``active`` subscription period end without further
                renewal)

        Default method works not the same as this approach, so if it is a
        `trialing` subscription - it cancels it immediately and for `active`
        ones - at period end. So we remove in this method related to trial
        period logic.

        """
        # make subscription cancel at period end date
        if at_period_end:
            stripe_subscription = self.api_retrieve()
            stripe_subscription.cancel_at_period_end = True
            stripe_subscription.save()
        # otherwise remove subscription
        else:
            try:
                stripe_subscription = self._api_delete()
            except InvalidRequestError as exc:
                if "No such subscription:" in str(exc):
                    # cancel() works by deleting the subscription. The object
                    # still exists in Stripe however, and can still be
                    # retrieved. If the subscription was already canceled
                    # (status=canceled), that api_retrieve() call will fail
                    # with "No such subscription".
                    # However, this may also happen if the subscription
                    # legitimately  does not exist, in which case the following
                    # line will re-raise.
                    stripe_subscription = self.api_retrieve()
                else:
                    raise

        return Subscription.sync_from_stripe_data(stripe_subscription)

    def reactivate_subscription(self) -> 'Subscription':
        """Reactivate current available subscription"""
        try:
            return self.reactivate()
        except stripe.error.StripeError as e:
            logger.error(
                f"Couldn't reactivate a subscription: {e}"
                f"{self.id} subscription for customer {self.customer.id}"
            )

    @classmethod
    def get_cancel_date(cls, sub: 'Subscription') -> Optional[datetime]:
        """Return `cancel_date` if subscription was canceled

        The method allows to handle `Subscription` objects (dj-stripe) and to
        avoid an additional call ORM for getting `SubscriptionProxy`

        """
        if sub.cancel_at_period_end:
            return sub.current_period_end

    @classmethod
    def get_renewal_date(cls, sub: 'Subscription') -> Optional[datetime]:
        """Return `renewal_date` for Subscription

        If the promo period is not applied - return current_period_end +
        18 month

        """
        if sub.customer.subscriber.finance_profile.was_promo_period_provided:
            return sub.current_period_end
        return calculate_promo_subscription_period(
            start_date=sub.current_period_end,
        )

    @property
    def is_trialing(self):
        """Check that subscription has trial state"""
        return self.status == SubscriptionStatus.trialing

    @property
    def is_active(self):
        """Check that subscription has active state"""
        return self.status == SubscriptionStatus.active

    @property
    def is_canceled(self):
        """Check that subscription is cancel"""
        return self.cancel_at_period_end or self.canceled_at


class CustomerProxy(Customer):
    """Proxy for `Customer` djstripe model."""

    class Meta:
        proxy = True
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')

    @classmethod
    def create_with_payment_data(
        cls, user, payment_method: str, set_default=True
    ) -> Customer:
        """Create Customer and attach payment method"""
        try:
            customer, created = cls.get_or_create(
                subscriber=user,
            )
            customer.add_payment_method(payment_method, set_default)
        except stripe.error.StripeError as e:
            logger.error(e)
            raise PaymentProfileCreationError(e.user_message)
        return customer

    @classmethod
    def create_with_card_data(cls, user, source: str) -> Customer:
        """Create Customer and attach card data"""
        try:
            customer, created = cls.get_or_create(
                subscriber=user,
            )
            customer.add_card(source)
        except stripe.error.StripeError as e:
            logger.error(e)
            raise PaymentProfileCreationError(e.user_message)
        return customer

    @cached_property
    #def current_subscription(self) -> 'SubscriptionProxy':
    #    """Return current valid subscription"""
    #    return self.subscriber.active_subscription

    @cached_property
    def next_subscription(self) -> Optional['SubscriptionProxy']:
        """Return next subscription instance.

        It is actual for `v1` subscription types.

        As a `next subscription` is considered not current subscription with a
        `trialing` status.

        """
        return
        #active_subscription = self.subscriber.active_subscription
        active_subscription_id = (
            active_subscription and active_subscription.id or None
        )
        return SubscriptionProxy.objects.filter(
            customer=self,
            status=SubscriptionStatus.trialing,
        ).exclude(id=active_subscription_id).last()
