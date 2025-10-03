"""Module store stripe helpers"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.utils.timezone import now

import arrow
from djstripe.models import Customer, Subscription

from apps.finance.exceptions import (
    InvalidSubscriptionAction,
    SubscriptionCreationError,
)
from apps.finance.models import PlanProxy

from ..models import CustomerProxy, SubscriptionProxy

if TYPE_CHECKING:
    from apps.users.models import AppUser


class StripeSubscriptionsService(object):
    """Base class to provide stripe `subscriptions` workflow functionality."""

    def __init__(self, user: AppUser, *args, **kwargs) -> None:
        self.customer = user.customer
        #self.subscription = user.active_subscription

    def verify_subscription(self, is_canceled=False):
        """Check that user have active subscription"""
        if not self.subscription or not self.subscription.is_valid():
            raise InvalidSubscriptionAction
        # if we validate that subscription is canceled and it is not - raise
        # error
        if is_canceled and not self.subscription.is_canceled:
            raise InvalidSubscriptionAction
        # validate that other subscriptions are not canceled
        elif not is_canceled and self.subscription.is_canceled:
            raise InvalidSubscriptionAction

    @staticmethod
    def date_to_timestamp(dt: date):
        """Shortcut to convert `dt` date to timestamp appropriate for stripe.
        """
        return int(arrow.get(dt).timestamp) if dt else None

    @classmethod
    def create_initial_subscription(
        cls, user: AppUser, trial_end: date = None
    ):
        """Create first paid subscription for user JLP

        Args:
            user (AppUser): user have related customer
            trial_end (date): date when user will start to pay for
                subscription (trial ends date)

        """
        try:
            customer = user.customer
            profile = user.finance_profile
            SubscriptionProxy.create(
                customer_id=customer.id,
                plan_id=profile.initial_plan_id,  # type: str
                trial_end=cls.date_to_timestamp(trial_end)
            )
            # update user FinanceProfile after successful subscription
            # creation with `trial`
            profile.was_promo_period_provided = True
            profile.save()
        except Exception as e:
            raise SubscriptionCreationError(e)

    @classmethod
    def create_customer_with_attached_card(
        cls, user: AppUser, payment_method: str, set_default=True
    ) -> Customer:
        """Service provide making stripe customer for mediator"""
        return CustomerProxy.create_with_payment_data(
            user=user, payment_method=payment_method, set_default=set_default
        )

    def cancel_current_subscription(self, at_period_end=False) -> Subscription:
        """Cancel current and next subscription(s)"""
        # self.verify_subscription()
        if not self.subscription or not self.subscription.is_valid():
            raise InvalidSubscriptionAction

        # cancel next subscription immediately
        if self.customer.next_subscription:
            self.customer.next_subscription.cancel_subscription(
                at_period_end=False
            )
        # cancel current user subscription
        return self.subscription.cancel_subscription(
            at_period_end=at_period_end
        )

    def reactivate_cancelled_subscription(self) -> Subscription:
        """Activate cancelled subscription"""
        self.verify_subscription(is_canceled=True)
        return self.subscription.reactivate_subscription()

    def change_subscription_plan(
            self, new_plan: PlanProxy,
    ) -> 'SubscriptionProxy':
        """Change a subscription by mediator

        1. mediator does not have subscription - create new instance
        2. If subscription is `trialing` - change plan immediately
        3. If current plan is premium - change current subscription immediately
        4. Otherwise, create next subscription after end billing period

        """
        # no subscription exists yet - create a new one
        if not self.subscription:
            return SubscriptionProxy.create(
                customer_id=self.customer.id,
                plan_id=new_plan.id,
            )

        self.verify_subscription()

        # change plan immediately for subscriptions with `trialing` status or
        # with `active` status when subscription switches to `premium` plan
        is_trialing = self.subscription.is_trialing
        is_active = self.subscription.is_active
        is_new_plan_premium = PlanProxy.check_is_premium(new_plan)
        if is_trialing or (is_active and is_new_plan_premium):
            return self.subscription.switching_plan_immediately(
                new_plan_id=new_plan.id
            )

        # switch plan at the end for `active` downgrade (premium -> standard)
        return self.subscription.switching_plan_at_end(new_plan_id=new_plan.id)

    def calc_subscription_changing_cost(self, new_plan: PlanProxy) -> dict:
        """Prepared data for updating subscription plan """
        if not self.subscription:
            return {
                'new_renewal_date': now(),
                'cost': new_plan.amount / 100
            }

        self.verify_subscription()

        # calculate proration cost for subscriptions with `trialing` status or
        # with `active` status when subscription switches to `premium` plan
        is_trialing = self.subscription.is_trialing
        is_active = self.subscription.is_active
        is_new_plan_premium = PlanProxy.check_is_premium(new_plan)
        if is_trialing or (is_active and is_new_plan_premium):
            cost, renewal_date = self.subscription.calculate_proration_cost(
                new_plan_id=new_plan.id,
            )
            return {
                'new_renewal_date': renewal_date,
                'cost': cost / 100
            }

        # calculated with checking promotional period whe subscription is
        # `active` and new plan is `standard`
        renewal_date = SubscriptionProxy.get_renewal_date(self.subscription)
        return {'new_renewal_date': renewal_date}


stripe_subscriptions_service = StripeSubscriptionsService
