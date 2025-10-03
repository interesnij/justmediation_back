import stripe
from health_check.exceptions import ServiceUnavailable
from stripe.error import StripeError
from .base import AbstractHealthCheckBackend


class StripeHealthCheck(AbstractHealthCheckBackend):
    """Check that stripe integration works alright."""
    _identifier = 'stripe'
    _description = 'Stripe Health Check'

    def check_status(self):
        """ Выполните простой вызов api для получения основной учетной записи и клиентов. """
        try:
            stripe.Account.retrieve()
            stripe.Customer.list()
        except StripeError as error:
            self.add_error(
                error=ServiceUnavailable(error.user_message), cause=error
            )
