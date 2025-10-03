import factory
from factory.fuzzy import FuzzyInteger
from faker import Faker

from apps.users.factories import AppUserFactory

from . import models

faker = Faker()


class ESignProfileFactory(factory.DjangoModelFactory):
    """Factory for EsignProfile model."""
    user = factory.SubFactory(AppUserFactory)
    docusign_id = factory.Faker('uuid4')

    class Meta:
        model = models.ESignProfile


class EnvelopeFactory(factory.DjangoModelFactory):
    """Factory for Envelope model."""
    docusign_id = factory.Faker('uuid4')
    matter = factory.SubFactory('apps.business.factories.MatterFactory')
    type = 'initial'

    class Meta:
        model = models.Envelope


class ESignDocumentFactory(factory.DjangoModelFactory):
    """Factory for ESignDocument model."""
    envelope = factory.SubFactory(EnvelopeFactory)
    name = factory.Faker('name')
    file = factory.django.ImageField(color='magenta')
    order = FuzzyInteger(0, 10)

    class Meta:
        model = models.ESignDocument
