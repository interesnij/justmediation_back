from django.db.models import QuerySet
from apps.users.models.users import AppUser
from ....core.models import BaseModel
from ....users import models as user_models
from ....users import signals as user_signals
from ....users.models import Client, Invite
from .base import BaseNotificationResource


class OpportunitiesNotificationResource(BaseNotificationResource):
    """
    Класс уведомлений о возможностях работы адвокатом.
    Это уведомление отправляется адвокату каждый день, если в
    этот день для этого адвоката были созданы какие-либо возможности.
    Получатели: Только адвокаты
    В дизайне это тип уведомления `Новые возможности`.
    """
    signal = user_signals.new_opportunities_for_mediator
    instance_type = user_models.UserStatistic
    runtime_tag = 'new_opportunities'
    title = 'New opportunities'
    deep_link_template = '{base_url}/leads'
    id_attr_path: str = 'pk'
    web_content_template = (
        'notifications/users/new_opportunities/web.txt'
    )
    push_content_template = (
        'notifications/users/new_opportunities/push.txt'
    )
    email_subject_template = 'You have {{instance.count}} new opportunities.'
    email_content_template = (
        'notifications/users/new_opportunities/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get mediators user profile as queryset."""
        return user_models.AppUser.objects.filter(pk=self.instance.user.pk)


class SharedContactResource(BaseNotificationResource):
    """Notification class for mediator shared contacts.

    This notification is sent when a new contact is shared with mediator.

    Recipients: Only mediators

    """
    title = 'New Contact'
    id_attr_path: str = 'pk'
    email_subject_template = 'New contact shared'

    def __init__(self, instance: BaseModel, receiver_pks,   **kwargs):
        self.receiver_pks = receiver_pks
        self.user = None
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get mediators user profile as queryset."""
        return user_models.AppUser.objects.filter(pk__in=self.receiver_pks)


class NewSharedContactClientNotificationResource(SharedContactResource):
    """Notification class for mediator shared contacts.

    This notification is to mediator when an registered
    contact(Client) is shared with mediator

    Recipients: Only mediators
    """
    signal = user_signals.new_registered_contact_shared
    deep_link_template = '{base_url}/clients'
    web_content_template = (
        'notifications/users/new_client_shared/web.txt'
    )
    push_content_template = (
        'notifications/users/new_client_shared/push.txt'
    )
    email_content_template = (
        'notifications/users/new_client_shared/email.html'
    )
    instance_type = Client
    runtime_tag = 'new_registered_contact_shared'
    user = None

    def get_notification_extra_payload(self) -> dict:
        return {
            "name": self.instance.display_name,
            "email": self.instance.user.email,
            "phone": self.instance.user.phone,
            "is_pending": False,
            "id": self.instance.user_id
        }


class NewSharedContactInviteNotificationResource(SharedContactResource):
    """Notification class for mediator shared contacts.

    This notification is to mediator when an unregistered
    contact(Invite) is shared with mediator

    Recipients: Only mediators
    """
    signal = user_signals.new_unregistered_contact_shared
    instance_type = Invite
    runtime_tag = 'new_unregistered_contact_shared'
    deep_link_template = '{base_url}/invites'
    web_content_template = (
        'notifications/users/new_invite_shared/web.txt'
    )
    push_content_template = (
        'notifications/users/new_invite_shared/push.txt'
    )
    email_content_template = (
        'notifications/users/new_invite_shared/email.html'
    )
    user = None

    def get_notification_extra_payload(self) -> dict:
        return dict(
             name=self.instance.full_name,
             email=self.instance.email,
             phone=self.instance.user.phone,
             is_pending=True,
             id=str(self.instance.uuid)
        )


class AdminNewUserRegisteredNotificationResource(BaseNotificationResource):
    """ Класс уведомлений для уведомления о регистрации для администратора.
    Это уведомление предназначено для уведомления администратора пользователя 
    всякий раз, когда адвокат или помощник юриста, или предприятие зарегистрированы
    Recipients: admin(support@justmediationhub.com)
    """ 
    signal = user_signals.new_user_registered
    title = 'New User'
    deep_link_template = '{base_url}/admin'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/users/new_user_registered/web.txt'
    )
    email_content_template = (
        'notifications/users/new_user_registered/email.html'
    ) 
    email_subject_template = (
        'A new user is registered'
    )
    instance_type = AppUser
    runtime_tag = 'new_user_registered'
    user = None

    def __init__(self, instance: AppUser, **kwargs):
        self.user = instance
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """ Получить профиль пользователя в качестве набора запросов ."""
        #return user_models.AppUser.objects.filter(
        #    email="interesnijsim49293@gmail.com" 
        #)
        return user_models.AppUser.objects.filter(
            is_staff=True 
        )

    def get_notification_extra_payload(self) -> dict:
        return dict(
            name=self.user.full_name,
        )
 