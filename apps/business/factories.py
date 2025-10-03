import random
from datetime import timedelta
from random import choice

from django.utils import timezone

import factory
from cities_light.models import City, Country, Region
from djstripe.enums import PaymentIntentStatus
from factory.fuzzy import FuzzyInteger
from faker import Faker

from ..finance.factories import PaymentIntentFactory
from ..finance.models import Payment
from ..forums.factories import TopicFactory
from ..users.factories import (
    AppUserWithMediatorFactory,
    MediatorFactory,
    ClientFactory,
)
from . import models
from .services import prepare_invoice_for_payment

faker = Faker()


class LeadFactory(factory.DjangoModelFactory):
    """Factory for Lead model."""
    topic = factory.SubFactory(TopicFactory)
    client = factory.SubFactory(ClientFactory)
    mediator = factory.SubFactory(MediatorFactory)

    class Meta:
        model = models.Lead


class MatterFactory(factory.DjangoModelFactory):
    """Factory for Matter model."""
    client = factory.SubFactory(ClientFactory)
    mediator = factory.SubFactory(MediatorFactory)
    code = factory.Faker('ean', length=13)
    title = factory.Faker('catch_phrase')
    description = factory.Faker('paragraph')
    rate = FuzzyInteger(50, 200)

    class Meta:
        model = models.Matter

    @factory.lazy_attribute
    def country(self):
        return Country.objects.first()

    @factory.lazy_attribute
    def state(self):
        return Region.objects.first()

    @factory.lazy_attribute
    def city(self):
        return City.objects.first()

    @factory.post_generation
    def add_related_models(self, *args, **kwargs):
        """Set related models.

        We doing this in post generation, so that matter's mediator matched
        with lead's and stage's mediators.

        """
        if not self.lead:
            self.lead = LeadFactory(
                mediator=self.mediator, client=self.client, topic=None
            )

        if not self.stage:
            self.stage = StageFactory(mediator=self.mediator)


class FullMatterFactory(MatterFactory):
    """Matter with related models."""
    notes = factory.RelatedFactoryList(
        'apps.business.factories.NoteFactory',
        'matter',
        size=2
    )
    billing_item = factory.RelatedFactoryList(
        'apps.business.factories.BillingItemFactory',
        'matter',
        size=2
    )
    shared_with = factory.RelatedFactoryList(
        'apps.business.factories.MatterSharedWithFactory',
        'matter',
        size=1
    )


class BillingItemFactory(factory.DjangoModelFactory):
    """Factory for BillingItem model."""
    matter = factory.SubFactory(MatterFactory)
    description = factory.Faker('paragraph')
    fees = FuzzyInteger(50, 100)
    time_spent = timedelta
    created_by = factory.SubFactory(AppUserWithMediatorFactory)

    class Meta:
        model = models.BillingItem

    @factory.lazy_attribute
    def time_spent(self):
        return timedelta(minutes=random.randint(15, 120))

    @factory.lazy_attribute
    def date(self, *args, **kwargs):
        """Set period_start."""
        return faker.date_time_between(
            start_date="-10d",
            tzinfo=timezone.utc
        ).date()

    @factory.lazy_attribute
    def created_by(self, *args, **kwargs):
        """Set period_start."""
        return self.matter.mediator.user


class InvoiceFactory(factory.DjangoModelFactory):
    """Factory for Invoice model."""
    matter = factory.SubFactory(MatterFactory)
    title = factory.Faker('catch_phrase')
    note = factory.Faker('paragraphs')
    created_by = factory.SubFactory(AppUserWithMediatorFactory)

    class Meta:
        model = models.Invoice

    @factory.lazy_attribute
    def period_start(self, *args, **kwargs):
        """Set period_start."""
        return faker.date_time_between(
            start_date='-1d',
            tzinfo=timezone.utc
        ).date()

    @factory.lazy_attribute
    def period_end(self, *args, **kwargs):
        """Set period_end."""
        period_start = self.period_start
        return period_start + timedelta(weeks=4)


class InvoiceWithTBFactory(InvoiceFactory):
    """Generate invoice with time billings."""

    @factory.post_generation
    def time_billings(obj: models.Invoice, *args, **kwargs):
        """Generate time billings for invoice"""
        BillingItemFactory.create_batch(
            matter=obj.matter,
            date=obj.period_start,
            created_by_id=obj.created_by_id,
            size=2,
        )


class ToBePaidInvoice(InvoiceFactory):
    """Generate invoice that will be paid."""
    status = models.Invoice.INVOICE_STATUS_OPEN
    payment_status = models.Invoice.PAYMENT_STATUS_IN_PROGRESS

    @factory.post_generation
    def time_billings(obj: models.Invoice, *args, **kwargs):
        """Generate time billings for to be paid invoice"""
        BillingItemAttachmentFactory.create_batch(
            invoice=obj,
            time_billing__matter=obj.matter,
            time_billing__date=obj.period_start,
            time_billing__created_by_id=obj.created_by_id,
            size=2,
        )
        prepare_invoice_for_payment(obj)
        payment_intent = PaymentIntentFactory(amount=int(obj.fees_earned))
        obj.payment = Payment.objects.create(
            amount=int(obj.fees_earned),
            payment_content_object=payment_intent,
            description=f'Payment for {obj}',
            payer_id=obj.matter.client_id,
            recipient_id=obj.matter.mediator_id,
        )
        obj.save()


class PaidInvoiceFactory(InvoiceFactory):
    """Generate paid invoice."""
    status = models.Invoice.INVOICE_STATUS_OPEN
    payment_status = models.Invoice.PAYMENT_STATUS_PAID

    @factory.post_generation
    def time_billings(obj: models.Invoice, *args, **kwargs):
        """Generate time billings for paid invoice"""
        created_by = obj.matter.mediator.user
        BillingItemAttachmentFactory.create_batch(
            invoice=obj,
            time_billing__matter=obj.matter,
            time_billing__date=obj.period_start,
            time_billing__created_by=created_by,
            size=2,
        )
        prepare_invoice_for_payment(obj)
        payment_intent = PaymentIntentFactory(
            amount=int(obj.fees_earned),
            status=PaymentIntentStatus.succeeded,
        )
        obj.payment = Payment.objects.create(
            amount=int(obj.fees_earned),
            payment_content_object=payment_intent,
            description=f'Payment for {obj}',
            status=Payment.STATUS_SUCCEEDED,
            payer_id=obj.matter.client_id,
            recipient_id=obj.matter.mediator_id,
        )
        obj.save()


class BillingItemAttachmentFactory(factory.DjangoModelFactory):
    """Factory for BillingItemAttachment model."""
    time_billing = factory.SubFactory(BillingItemFactory)
    invoice = factory.SubFactory(InvoiceFactory)

    class Meta:
        model = models.BillingItemAttachment


class ActivityFactory(factory.DjangoModelFactory):
    """Factory for Activity model."""
    matter = factory.SubFactory(MatterFactory)
    title = factory.Faker('catch_phrase')

    class Meta:
        model = models.Activity


class NoteFactory(factory.DjangoModelFactory):
    """Factory for Note model."""
    matter = factory.SubFactory(MatterFactory)
    title = factory.Faker('catch_phrase')
    text = factory.Faker('paragraph')
    created_by = factory.SubFactory(AppUserWithMediatorFactory)

    class Meta:
        model = models.Note

    @factory.lazy_attribute
    def created_by(self):
        return choice([self.matter.mediator.user, self.matter.client.user])


class StageFactory(factory.DjangoModelFactory):
    """Factory for `Stage` model."""
    title = factory.Faker('paragraph')
    mediator = factory.SubFactory(MediatorFactory)

    class Meta:
        model = models.Stage


class ChecklistEntryFactory(factory.DjangoModelFactory):
    """Factory for `ChecklistEntry` model."""
    description = factory.Faker('paragraph')
    mediator = factory.SubFactory(MediatorFactory)

    class Meta:
        model = models.ChecklistEntry


class MatterTopicFactory(factory.DjangoModelFactory):
    """Factory for `MatterTopic` model."""
    matter = factory.SubFactory(MatterFactory)
    title = factory.Faker('word')

    class Meta:
        model = models.MatterTopic


class MatterPostFactory(factory.DjangoModelFactory):
    """Factory for `MatterPost` model."""
    topic = factory.SubFactory(MatterTopicFactory)
    author = factory.SubFactory(AppUserWithMediatorFactory)
    text = factory.Faker('text')

    class Meta:
        model = models.MatterPost


class VoiceConsentFactory(factory.DjangoModelFactory):
    """Factory for `VoiceConsent` model."""
    matter = factory.SubFactory(MatterFactory)
    title = factory.Faker('ean', length=13)
    file = factory.django.FileField(filename='voice_consent.mp3')

    class Meta:
        model = models.VoiceConsent


class MatterSharedWithFactory(factory.DjangoModelFactory):
    """Factory for `MatterSharedWith` model."""
    matter = factory.SubFactory(MatterFactory)
    user = factory.SubFactory(AppUserWithMediatorFactory)

    class Meta:
        model = models.MatterSharedWith

    @factory.post_generation
    def verify_mediator(self, *arg, **kwargs):
        """Verify user's mediator."""
        if self.user.is_mediator:
            self.user.mediator.verify_by_admin()
