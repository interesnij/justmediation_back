import factory

from apps.users.factories import (
    AppUserFactory,
    ClientFactory,
    SpecialityFactory,
)

from . import models


class CategoryFactory(factory.DjangoModelFactory):
    """Factory for Category model."""
    speciality = factory.SubFactory(SpecialityFactory)
    title = factory.Faker('catch_phrase')
    description = factory.Faker('paragraph')
    icon = factory.django.ImageField(color='magenta')

    class Meta:
        model = models.Category


class PostFactory(factory.DjangoModelFactory):
    """Factory for Post model
    """

    topic = factory.SubFactory('apps.forums.factories.TopicFactory')
    text = factory.Faker('paragraph')

    class Meta:
        model = models.Post

    @factory.lazy_attribute
    def author(self):
        return ClientFactory().user


class TopicFactory(factory.DjangoModelFactory):
    """Factory for Topic model
    """
    category = factory.SubFactory(CategoryFactory)
    title = factory.Faker('catch_phrase')

    class Meta:
        model = models.Topic


class FollowedTopicFactory(factory.DjangoModelFactory):
    """Factory for FollowedTopic model."""
    follower = factory.SubFactory(AppUserFactory)
    topic = factory.SubFactory(TopicFactory)

    class Meta:
        model = models.FollowedTopic


class UserStatsFactory(factory.DjangoModelFactory):
    """Factory for UserStats model."""
    user = factory.SubFactory(AppUserFactory)

    class Meta:
        model = models.UserStats
