import json
from datetime import datetime

from django.db.models import QuerySet

from ....core.models import BaseModel
from ....social import models as social_models
from ....social import signals as social_signals
from ....users import models as user_models
from . import BaseNotificationResource


class NewSingleGroupChatResource(BaseNotificationResource):
    """Notification class for invitations to group chats.

    This notification is sent to participants of group chats, when
    they are invited or if they were mentioned on group chat creation.

    Recipients: AppUser

    """
    signal = social_signals.added_to_new_chat
    instance_type = social_models.Chats
    runtime_tag = 'new_chat'
    title = 'New Chat Created'
    deep_link_template = '{base_url}/social/chats/{id}/'
    id_attr_path = 'pk'
    web_content_template = (
        'notifications/social/new_chat/web.txt'
    )
    push_content_template = (
        'notifications/social/new_chat/push.txt'
    )
    email_subject_template = 'Invitation to a network.'
    email_content_template = (
        'notifications/social/new_chat/email.html'
    )

    def __init__(
        self,
        instance: BaseModel,
        invited,
        inviter: user_models.AppUser,
        current_site: str = "",
        message: str = None,
        **kwargs
    ):
        """Add invited to class."""
        self.invited = invited
        self.inviter = inviter
        self.message = message
        self.current_site = current_site
        self.user = inviter
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get all invited participants as queryset."""
        return user_models.AppUser.objects.filter(
            pk__in=self.invited
        ).exclude(pk=self.inviter.pk)

    def get_notification_extra_payload(self) -> dict:
        """Add message to notification's extra payload."""
        return dict(
            message=self.message,
            current_site=self.current_site,
            user_name=self.inviter.full_name,
            user_type=self.inviter.user_type
        )


class NewChatResource(BaseNotificationResource):
    """ Notification class for new chat message.
    This notification is sent to participants of group chats, when
    they are invited or if they were mentioned on group chat creation.
    Recipients: AppUser
    """
    signal = social_signals.new_chat_message
    instance_type = social_models.Message
    runtime_tag = 'new_chat_message'
    title = 'New Message'
    deep_link_template = '{base_url}/social/chats/{id}/'
    id_attr_path = 'pk'
    web_content_template = (
        'notifications/social/new_chat_message/web.txt'
    )
    push_content_template = (
        'notifications/social/new_chat_message/push.txt'
    )
    email_subject_template = 'New message from {{instance.author.full_name}}'
    email_content_template = (
        'notifications/social/new_chat_message/email.html'
    )

    def __init__(
        self,
        instance: BaseModel,
        inviter: user_models.AppUser,
        **kwargs
    ):
        """Add invited to class."""
        self.inviter = inviter
        self.type = instance.type
        if instance.type == 'text':
            self.message = instance.text
        elif instance.type == 'endCall':
            call_at = json.loads(instance.text)['callStartedAt']
            call_at = datetime.strptime(call_at, '%Y-%m-%dT%H:%M:%S.%fZ').\
                replace(microsecond=0)
            self.message = f'{inviter.full_name} ' \
                f'send you a Video Call request at {call_at}'
        else:
            self.message = f'{inviter.full_name} send you a voice message'
        self.user = inviter
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get all invited participants as queryset."""
        return user_models.AppUser.objects.filter(
            pk__in=self.instance.chat.participants.values_list('pk')
        ).exclude(pk=self.inviter.pk)

    def get_notification_extra_payload(self) -> dict:
        """Add message to notification's extra payload."""
        return dict(
            type=self.type,
            message=self.message,
            user_name=self.inviter.full_name,
            author_name=self.instance.author.full_name,
            user_type=self.inviter.user_type
        )
