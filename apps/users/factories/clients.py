import random

import factory
from cities_light.management.commands import cities_light

from ...users import models


class ClientFactory(factory.DjangoModelFactory):
    user = factory.SubFactory('apps.users.factories.AppUserFactory')
    help_description = factory.Faker('paragraph')

    class Meta:
        model = models.Client

    @factory.lazy_attribute
    def state(self, *args, **kwargs):
        """Set clients state."""
        if cities_light.Region.objects.exists():
            return random.choice(cities_light.Region.objects.all())
