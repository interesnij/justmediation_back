import random
from datetime import timedelta
from django.utils import timezone
import factory
from djstripe.models import PaymentMethod
from factory.fuzzy import FuzzyInteger
from faker import Faker
from . import models
from .constants import Capabilities
from .models import AccountProxyInfo, PaymentIntentProxy

faker = Faker()


class ProductProxyFactory(factory.DjangoModelFactory):
    """Factory for ProductProxy model."""
    id = factory.Faker('uuid4')
    name = factory.Faker('word')
    type = 'service'
    active = True
    description = factory.Faker('catch_phrase')

    class Meta:
        model = models.ProductProxy


class PlanProxyFactory(factory.DjangoModelFactory):
    """Factory for PlanProxy model."""
    id = factory.Faker('uuid4')
    product = factory.SubFactory(ProductProxyFactory)
    active = True
    billing_scheme = 'per_unit'
    currency = 'usd'
    interval = 'year'
    usage_type = 'licensed'
    amount = FuzzyInteger(35000, 100000)  # $350 - $1000
    metadata = {}

    class Meta:
        model = models.PlanProxy


class PaymentMethodFactory(factory.DjangoModelFactory):
    """Factory for PaymentMethod model."""
    id = factory.Faker('uuid4')
    billing_details = {}
    card = {}

    class Meta:
        model = PaymentMethod


class CustomerProxyFactory(factory.DjangoModelFactory):
    """Factory for CustomerProxy model."""
    id = factory.Faker('uuid4')
    subscriber = factory.SubFactory('apps.users.factories.AppUserFactory')
    balance = random.randint(1000, 10000)
    delinquent = False
    default_payment_method = factory.SubFactory(PaymentMethodFactory)

    class Meta:
        model = models.CustomerProxy


class SubscriptionProxyFactory(factory.DjangoModelFactory):
    """Factory for SubscriptionProxy model."""
    id = factory.Faker('uuid4')
    customer = factory.SubFactory(CustomerProxyFactory)

    class Meta:
        model = models.SubscriptionProxy

    @factory.lazy_attribute
    def start(self, *args, **kwargs):
        """Set current_period_start."""
        return faker.date_time_between(
            start_date='-1d',
            tzinfo=timezone.utc
        )

    @factory.lazy_attribute
    def current_period_start(self, *args, **kwargs):
        """Set current_period_start."""
        return self.start

    @factory.lazy_attribute
    def current_period_end(self, *args, **kwargs):
        """Set current_period_end."""
        return self.current_period_start + timedelta(weeks=4)


class AccountProxyFactory(factory.DjangoModelFactory):
    """Factory for AccountProxy model."""
    id = factory.Faker('uuid4')
    details_submitted = True
    charges_enabled = True
    payouts_enabled = True

    class Meta:
        model = models.AccountProxy


class VerifiedAccountProxyFactory(AccountProxyFactory):
    """Factory for verified AccountProxy model."""
    requirements = {
        'eventually_due': [], 'pending_verification': []
    }

    @factory.post_generation
    def verify(self, *args, **kwargs):
        """Make account verified."""
        info, _ = AccountProxyInfo.objects.get_or_create(
            account=self
        )
        info.capabilities = {
            capability: 'active' for capability in Capabilities.default
        }
        info.save()


class FinanceProfileFactory(factory.DjangoModelFactory):
    """Factory for FinanceProfile model."""
    user = factory.SubFactory(
        'apps.users.factories.AppUserWithMediatorFactory'
    )
    deposit_account = factory.SubFactory(AccountProxyFactory)

    class Meta:
        model = models.FinanceProfile

    @factory.post_generation
    def customer(self, *args, **kwargs):
        """Generate stripe customer for a user."""
        CustomerProxyFactory(subscriber=self.user)


class FinanceProfileFactoryWithVerifiedAccount(FinanceProfileFactory):
    """Factory for FinanceProfile model with verified account."""
    deposit_account = factory.SubFactory(VerifiedAccountProxyFactory)


class PaymentIntentFactory(factory.DjangoModelFactory):
    """Factory for PaymentIntent model."""
    id = factory.Faker('uuid4')
    currency = 'usd'
    amount = FuzzyInteger(35000, 100000)  # $350 - $1000
    amount_capturable = 0
    amount_received = 0

    class Meta:
        model = PaymentIntentProxy
