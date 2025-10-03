from django.db.models import QuerySet

from ....core.models import BaseModel
from ....promotion import models as promotion_models
from ....promotion import signals as promotion_signals
from ....users import models as user_models
from .base import BaseNotificationResource


class NewMediatorEventNotificationResource(BaseNotificationResource):
    """Notification class for mediator events.

    This notification is sent to mediator' followers, when mediator creates
    new event.

    Recipients: Only client

    In designs it's `New Event` notification type of group
    'mediators I Follow'.

    """
    signal = promotion_signals.new_mediator_event
    instance_type = promotion_models.Event
    runtime_tag = 'new_mediator_event'
    title = 'New mediator event'
    deep_link_template = '{base_url}/mediators/profile/{id}'
    id_attr_path: str = 'mediator_id'
    web_content_template = (
        'notifications/promotion/new_event/web.txt'
    )
    push_content_template = 'notifications/promotion/new_event/push.txt'
    email_subject_template = (
        'New event added by {{instance.mediator.display_name}}'
    )
    email_content_template = 'notifications/promotion/new_event/email.html'

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        if instance.mediator:
            self.user: user_models.AppUser = instance.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get mediator' followers."""
        if self.instance.mediator:
            return self.instance.mediator.followers.all()
