from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Q
from .querysets import AppUserQuerySet


class AppUserManager(BaseUserManager.from_queryset(AppUserQuerySet)):
    """ Пользовательский менеджер, который не использует имя пользователя. """

    def create_user(self, email, password, **extra_fields):
        """ Создайте пользователя, но без использования имени пользователя. """
        if not email:
            raise ValueError('Enter an email address')
        if not password:
            raise ValueError('Enter password')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        """ Создайте суперпользователя без использования имени пользователя. """
        user = self.create_user(
            email,
            password=password,
            is_superuser=True,
            is_staff=True,
            **kwargs
        )
        return user

    def had_business_with(self, user):
        """ Получите всех пользователей приложения, с которыми у пользователя были какие-то дела.
        Для адвоката:
            Имел дело с клиентом или лидом.
            Приглашенный пользователь
        Для клиента:
            Имел дело с адвокатом.
            Был приглашен адвокатом

        """
        mediator_matter_filter = Q(client__matters__mediator_id=user.pk)
        mediator_client_lead_filter = Q(client__leads__mediator_id=user.pk)
        mediator_invite_filter = Q(invitations__inviter_id=user.pk)

        client_matter_filter = Q(mediator__matters__client_id=user.pk)
        client_client_lead_filter = Q(mediator__leads__client_id=user.pk)
        client_invite_filter = Q(sent_invitations__user_id=user.pk)

        return self.filter(
            mediator_matter_filter |
            mediator_client_lead_filter |
            mediator_invite_filter |
            client_matter_filter |
            client_client_lead_filter |
            client_invite_filter
        ).distinct()
