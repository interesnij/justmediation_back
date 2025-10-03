import logging
from typing import Union

from django.conf import settings

import stripe
from stripe.oauth import OAuth

from ..constants import Capabilities

logger = logging.getLogger('stripe')


class StripeDepositsService:
    """Base class to provide stripe `deposits` workflow functionality.

    Methods of this class are mostly related to Stripe Connect API.
        https://stripe.com/docs/connect/

    """

    @staticmethod
    def get_authorization_url(state: str, user: 'AppUser') -> str:  # noqa
        """Prepare authorization url to create Stripe `express` Account.

        Args:
            state (str): unique user identifier on backend to match returned
                in callback one
            user(AppUser): user for which Express account is created

        Returns:
            (str): authorization url to which user should be redirected to
                proceed Express account creation

        """
        return OAuth.authorize_url(
            express=True,
            **{
                'client_id': settings.STRIPE_CONNECT_CLIENT_ID,
                'state': state,
                'suggested_capabilities': Capabilities.default,
                'stripe_user[email]': user.email,
                'stripe_user[country]': 'US',
                'stripe_user[phone_number]': user.phone,
                'stripe_user[first_name]': user.first_name,
                'stripe_user[last_name]': user.last_name,
            }
        )

    @staticmethod
    def get_token(code: str) -> dict:
        """Shortcut to get token by `code` from Stripe.

        Arguments:
            code (str): returned in oAuth callback authorization code

        Returns:
            (dict): params of successful account authorization

        """
        return OAuth.token(
            grant_type='authorization_code',
            code=code,
            # check  that capabilities were really applied
            assert_capabilities=Capabilities.default
        )

    @classmethod
    def get_finance_profile(
        cls, account_id: str
    ) -> Union['FinanceProfile', None]:  # noqa
        """Shortcut to get `finance` profile by `account_id`"""
        from ..models import FinanceProfile

        finance_profile = FinanceProfile.objects.filter(
            deposit_account__id=account_id
        ).first()
        if not finance_profile:
            logger.info(
                f'Get `account` webhook for account not linked to any '
                f'DB user {account_id}'
            )
            return
        return finance_profile

    @classmethod
    def update_capability(
        cls, account: 'AccountProxy', capability_id: str  # noqa
    ):
        """Update `capability` info for some account."""
        data = stripe.Account.retrieve_capability(account.id, capability_id)
        capabilities = account.info.capabilities

        is_active = data['status'] == 'active'
        has_pending_info = data['requirements']['pending_verification']

        # do nothing if `status` became active, but capability still needs
        # some info
        if is_active and has_pending_info:
            return

        capabilities[capability_id] = data['status']
        account.info.save()


stripe_deposits_service = StripeDepositsService
