import factory
from constance import config
from djstripe.enums import PaymentIntentStatus

from ...finance.factories import PaymentIntentFactory
from ...finance.models import Payment
from ...users import models


class SupportFactory(factory.DjangoModelFactory):
    """Factory for `Support` user model."""
    user = factory.SubFactory('apps.users.factories.AppUserFactory')
    description = factory.Faker('word')

    class Meta:
        model = models.Support


class SupportVerifiedFactory(SupportFactory):
    """Create verified support user."""

    @factory.post_generation
    def verify_support(obj: models.Support, create, extracted, **kwargs):
        """Verify created user."""
        obj.verify()
        obj.save()


class SupportVerifiedWithPaymentFactory(SupportVerifiedFactory):
    """Create verified support user with payment."""
    payment_status = models.Support.PAYMENT_STATUS_IN_PROGRESS

    @factory.post_generation
    def add_payment(obj: models.Support, create, extracted, **kwargs):
        payment_intent = PaymentIntentFactory(
            amount=int(config.USER_FEE),
            status=PaymentIntentStatus.requires_payment_method,
        )
        obj.payment = Payment.objects.create(
            amount=config.USER_FEE,
            payment_content_object=payment_intent,
            description=f'Payment for {obj}',
            status=Payment.STATUS_IN_PROGRESS,
            payer_id=obj.pk,
        )
        obj.save()


class PaidSupportFactory(SupportVerifiedFactory):
    """Create verified support user with succeeded payment."""
    payment_status = models.Support.PAYMENT_STATUS_PAID

    @factory.post_generation
    def add_payment(obj: models.Support, create, extracted, **kwargs):
        payment_intent = PaymentIntentFactory(
            amount=int(config.USER_FEE),
            status=PaymentIntentStatus.succeeded,
        )
        obj.payment = Payment.objects.create(
            amount=config.USER_FEE,
            payment_content_object=payment_intent,
            description=f'Payment for {obj}',
            status=Payment.STATUS_SUCCEEDED,
            payer_id=obj.pk,
        )
        obj.save()
