import random
from datetime import timedelta

import factory
import pytz
from faker import Faker

from ..promotion import models

faker = Faker()


class EventFactory(factory.DjangoModelFactory):
    """Factory for generating test `Event` model."""

    title = factory.Faker('text')
    description = factory.Faker('text')
    location = factory.Faker('address')

    mediator = factory.SubFactory(
        'apps.users.factories.MediatorFactory'
    )

    class Meta:
        model = models.Event

    @factory.lazy_attribute
    def start(self, *args, **kwargs):
        """Set start time of event."""
        tz = pytz.timezone(random.choice(list(pytz.all_timezones_set)))
        return faker.date_time_between(
            start_date="+1h",
            end_date="+1m",
            tzinfo=tz
        )

    @factory.lazy_attribute
    def end(self, *args, **kwargs):
        """Set end time of event."""
        start = self.start
        return start + timedelta(hours=faker.pyint(min_value=1, max_value=3))
