import factory

from .models import (
    Notification,
    NotificationDispatch,
    NotificationGroup,
    NotificationSetting,
    NotificationType,
)


class NotificationFactory(factory.DjangoModelFactory):
    """Factory for generating test `Notification` model.

    TODO: add content object generation

    """
    title = factory.Faker('paragraph')
    type = factory.SubFactory(
        'apps.notifications.factories.NotificationTypeFactory'
    )
    notification_dispatches = factory.RelatedFactoryList(
        'apps.notifications.factories.NotificationDispatchFactory',
        'notification',
        size=2
    )

    class Meta:
        model = Notification


class NotificationDispatchFactory(factory.DjangoModelFactory):
    """Factory for generating relationship between user and notification."""

    notification = factory.SubFactory(NotificationFactory)
    recipient = factory.SubFactory('apps.users.factories.AppUserFactory')

    class Meta:
        model = NotificationDispatch


class NotificationTypeFactory(factory.DjangoModelFactory):
    """Factory for generating test `NotificationType` model."""
    title = factory.Faker('paragraph', nb_sentences=1)

    group = factory.SubFactory(
        'apps.notifications.factories.NotificationGroupFactory'
    )

    class Meta:
        model = NotificationType

    @factory.lazy_attribute
    def runtime_tag(self):
        """Generate tag for notification type."""
        # TODO: update this when it become clearer how we'll generate it
        return self.title.lower().replace(' ', '_')[:50]


class NotificationGroupFactory(factory.DjangoModelFactory):
    """Factory for generating test `NotificationGroup` model."""
    title = factory.Faker('paragraph', nb_sentences=1)

    types = factory.RelatedFactoryList(
        NotificationTypeFactory,
        'group',
        size=2
    )

    class Meta:
        model = NotificationGroup


class NotificationsSettingFactory(factory.DjangoModelFactory):
    """Factory for generating test `NotificationSetting` model."""
    by_email = factory.Faker('pybool')
    by_push = factory.Faker('pybool')

    notification_type = factory.SubFactory(NotificationTypeFactory)
    user = factory.SubFactory('apps.users.factories.AppUserFactory')

    class Meta:
        model = NotificationSetting
