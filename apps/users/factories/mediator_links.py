import factory
from factory.fuzzy import FuzzyInteger

from ..models import (
    AppointmentType,
    MediatorEducation,
    MediatorRegistrationAttachment,
    Currencies,
    FeeKind,
    Language,
    PaymentType,
    Speciality,
    University,
)


class ModelWithTitleFactory(factory.DjangoModelFactory):
    """Factory for generating model with title."""
    title = factory.Faker('ean13')


class SpecialityFactory(ModelWithTitleFactory):
    """Factory for generating test Specialty model."""

    class Meta:
        model = Speciality


class FeeKindFactory(ModelWithTitleFactory):
    """Factory for generating test FeeKind model."""

    class Meta:
        model = FeeKind


class UniversityFactory(ModelWithTitleFactory):
    """Factory for generating test University model."""

    class Meta:
        model = University


class MediatorEducationFactory(factory.DjangoModelFactory):
    """Factory for generating relationship between mediator and university."""
    university = factory.SubFactory(UniversityFactory)
    mediator = factory.SubFactory('mediator.MediatorFactory')
    year = FuzzyInteger(low=1990, high=2019)

    class Meta:
        model = MediatorEducation


class MediatorRegistrationAttachmentFactory(factory.DjangoModelFactory):
    """Factory for generating registration attachments for mediator."""
    mediator = factory.SubFactory('mediator.MediatorFactory')
    attachment = factory.django.ImageField(color='magenta')

    class Meta:
        model = MediatorRegistrationAttachment


class AppointmentTypeFactory(ModelWithTitleFactory):
    """Factory for generating test AppointmentType model."""

    class Meta:
        model = AppointmentType


class PaymentTypeFactory(ModelWithTitleFactory):
    """Factory for generating test PaymentType model."""

    class Meta:
        model = PaymentType


class LanguageFactory(ModelWithTitleFactory):
    """Factory for generating test Language model"""

    class Meta:
        model = Language


class CurrenciesFactory(ModelWithTitleFactory):
    """Factory for generating test Currencies model"""

    class Meta:
        model = Currencies
