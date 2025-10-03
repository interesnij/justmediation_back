import uuid

import factory

from ...users import models
from .mediators import MediatorFactoryWithAllInfo
from .clients import ClientFactory
from .support import SupportFactory


class AppUserFactory(factory.DjangoModelFactory):
    """Factory for generates test AppUser model.

    There are required fields first_name, last_name and email and password.

    """
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    avatar = factory.django.ImageField(color='magenta')

    password = factory.PostGenerationMethodCall('set_password', 'password')

    @factory.lazy_attribute
    def email(self):
        """Return formatted email."""
        return "{0}@example.com".format(uuid.uuid4())

    class Meta:
        model = models.AppUser


class AppUserWithMediatorFactory(AppUserFactory):
    """Create user with mediator information."""

    @factory.post_generation
    def mediator_info(self, *arg, **kwargs):
        """Add mediator to user."""
        self.mediator = MediatorFactoryWithAllInfo(user=self)


class AppUserWithClientFactory(AppUserFactory):

    @factory.post_generation
    def client_info(self, *arg, **kwargs):
        """Add client to user."""
        self.client = ClientFactory(user=self)


class AppUserWithSupportFactory(AppUserFactory):

    @factory.post_generation
    def support_info(self, *arg, **kwargs):
        """Add support to user."""
        self.support = SupportFactory(user=self)


class AppUserWithAvatarFactory(AppUserFactory):
    """Custom factory for testing user with avatar.

    The factory creates really user avatar file.

    """
    avatar = factory.django.ImageField(color='magenta')


class AdminAppUserFactory(AppUserFactory):
    """Factory for generates test User model with admin's privileges."""

    is_superuser = True
    is_staff = True


class InviteFactory(factory.DjangoModelFactory):
    """Factory to generate test `Invite` model."""
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    message = factory.Faker('paragraphs')

    inviter = factory.SubFactory(
        'apps.users.factories.AppUserWithMediatorFactory'
    )

    class Meta:
        model = models.Invite

    @factory.lazy_attribute
    def email(self):
        """Return formatted email."""
        return "{0}@example.com".format(uuid.uuid4())
