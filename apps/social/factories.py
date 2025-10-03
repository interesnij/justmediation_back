import factory

from . import models


class GroupChatFactory(factory.DjangoModelFactory):
    """Factory for generating test `GroupChat`."""

    title = factory.Faker('text')
    creator = factory.SubFactory(
        'apps.users.factories.AppUserWithMediatorFactory'
    )

    class Meta:
        model = models.GroupChat


class MediatorPostFactory(factory.DjangoModelFactory):
    """Factory for MediatorPost model."""
    title = factory.Faker('catch_phrase')
    body = factory.Faker('paragraph')
    body_preview = factory.Faker('text', max_nb_chars=150)
    image = factory.django.ImageField(color='magenta')
    author = factory.SubFactory(
        'apps.users.factories.MediatorFactory'
    )

    class Meta:
        model = models.MediatorPost
