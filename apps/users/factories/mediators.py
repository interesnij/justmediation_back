import random

from django.contrib.gis.geos import Point
from django.test import override_settings

import factory
import faker
from cities_light.management.commands import cities_light
from factory.fuzzy import FuzzyDecimal, FuzzyInteger

from ..models import Mediator
from .mediator_links import (
    MediatorEducationFactory,
    FeeKindFactory,
    SpecialityFactory,
)

fake = faker.Faker()


class MediatorFactory(factory.DjangoModelFactory):
    """Factory for generating test Mediator model."""

    license_info = factory.Faker('text')
    extra_info = factory.Faker('text')
    speciality_time = FuzzyInteger(0)
    speciality_matters_count = FuzzyInteger(0)
    fee_rate = FuzzyDecimal(1, 100)
    charity_organizations = factory.Faker('text')
    have_speciality = True
    years_of_experience = FuzzyInteger(1, 20)
    firm_location_city = factory.Faker('city')
    firm_location_state = factory.Faker('state')
    firm_location_data = {}
    keywords = factory.Faker('words')
    registration_attachments = factory.RelatedFactoryList(
        'apps.users.factories.MediatorRegistrationAttachmentFactory',
        'mediator',
        size=2
    )

    user = factory.SubFactory('apps.users.factories.AppUserFactory')

    class Meta:
        model = Mediator

    @factory.lazy_attribute
    def firm_location(self):
        """Set mediator location."""
        return Point(random.randint(0, 180), random.randint(0, 90))

    @factory.lazy_attribute
    def phone(self):
        return fake.numerify('+12125552###')

    @factory.post_generation
    def extra_info(self, *args, **kwargs):
        """Fill Mediator with related models."""
        specialities = SpecialityFactory.create_batch(size=2)
        for speciality in specialities:
            self.user.specialities.add(speciality)

        regions = cities_light.Region.objects.all()
        if regions:
            self.practice_jurisdictions.set(random.choices(regions, k=2))


class MediatorVerifiedFactory(MediatorFactory):
    """Create verified mediator."""

    #user__active_subscription = factory.SubFactory(
    #    'apps.finance.factories.SubscriptionProxyFactory'
    #)

    @factory.post_generation
    @override_settings(STRIPE_ENABLED=False)
    def verify_mediator(self: Mediator, create, extracted, **kwargs):
        """Set `STRIPE_ENABLED = False` for success verification"""
        #self.verify()
        #self.user.has_active_subscription = True
        #self.user.save()


class MediatorFactoryWithAllInfo(MediatorVerifiedFactory):
    """Create mediator with all information."""

    events = factory.RelatedFactoryList(
        'apps.promotion.factories.EventFactory',
        'mediator',
        size=3
    )
    checklist = factory.RelatedFactoryList(
        'apps.business.factories.ChecklistEntryFactory',
        'mediator',
        size=3
    )
    stages = factory.RelatedFactoryList(
        'apps.business.factories.StageFactory',
        'mediator',
        size=3
    )

    @factory.post_generation
    def extra_info(self: Mediator, *args, **kwargs):
        """Fill Mediator with related models."""
        specialities = SpecialityFactory.create_batch(size=2)
        for speciality in specialities:
            self.user.specialities.add(speciality)

        regions = cities_light.Region.objects.all()
        self.practice_jurisdictions.set(random.choices(regions, k=2))

        fee_types = FeeKindFactory.create_batch(size=2)
        for fee_type in fee_types:
            self.fee_types.add(fee_type)

        educations = MediatorEducationFactory.create_batch(
            mediator=self,
            size=2
        )
        for education in educations:
            self.education.add(education)

        # Escape import error
        from .users import ClientFactory

        followers = ClientFactory.create_batch(size=2)
        for follower in followers:
            self.followers.add(follower.user)
