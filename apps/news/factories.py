import factory

from . import models


class NewsFactory(factory.DjangoModelFactory):
    """Factory for News model."""
    title = factory.Faker('catch_phrase')
    description = factory.Faker('paragraph')
    image = factory.django.ImageField(color='magenta')

    class Meta:
        model = models.News
