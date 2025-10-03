import logging
import pprint
from functools import partial

from django.db.models import QuerySet

from libs.utils import get_base_url

from ...notifications import models, querysets
from ...users.models import AppUser
from .resources import RESOURCE_MAPPING, BaseNotificationResource
from .sender import send_notification_by_email, send_notification_by_push
from .tools import get_allowed_to_notify

logger = logging.getLogger('django')


class NotificationDispatcher:
    """Used to send notifications to it's recipients.

    This class decides to whom notification will be dispatched(also creates
    NotificationDispatches) and how it will be dispatched(by email, by push or
    by both).

    Attributes:
        resource (BaseNotificationResource):
            notification resource used for data representation
        notification (Notification):
            Notification, which will be dispatched
        dispatches (NotificationDispatchQuery):
            Queryset of notification dispatches, that will be used for
            dispatching

    """

    def __init__(
        self,
        resource: BaseNotificationResource = None,
        notification: models.Notification = None,
        dispatches: querysets.NotificationDispatchQuery = None
    ):
        """Initiate notification dispatcher."""
        self.resource: BaseNotificationResource = resource
        self.notification: models.Notification = notification
        self.dispatches: QuerySet = dispatches

    def get_recipients(self) -> QuerySet:
        """Get recipients to which we allowed to send notifications."""
        assert self.resource, 'resource is not set'
        assert self.notification, 'notification is not set'
        return get_allowed_to_notify(
            recipients=self.resource.get_recipients(),
            runtime_tag=self.notification.type.runtime_tag
        )

    def create_notification_dispatches(
        self
    ) -> querysets.NotificationDispatchQuery:
        """Create notification dispatches queryset."""
        dispatches = models.NotificationDispatch.objects.bulk_create(
            models.NotificationDispatch(
                notification=self.notification,
                recipient=recipient,
                sender=self.resource.user
            )
            for recipient in self.get_recipients()
        )
        pks = [dispatch.pk for dispatch in dispatches]
        return models.NotificationDispatch.objects.filter(
            pk__in=pks
        )

    def get_notification_dispatches_queryset(
        self
    ) -> querysets.NotificationDispatchQuery:
        """Get notification dispatches queryset for dispatching."""
        dispatches = self.dispatches
        if not dispatches:
            dispatches = self.create_notification_dispatches()
        return dispatches.get_allowed_to_notify().select_related(
            'notification',
            'notification__type',
            'recipient'
        )

    def notify(self):
        """Send push and email notifications to recipients"""
        notification_dispatches = self.get_notification_dispatches_queryset()
        for dispatch in notification_dispatches:
            self.dispatch_notification(dispatch=dispatch)

    @classmethod
    def dispatch_notification(cls, dispatch: models.NotificationDispatch):
        """Dispatch notification to recipient."""
        notification = dispatch.notification
        notification.extra_payload['user_name'] = ' '.join(
            [dispatch.recipient.first_name, dispatch.recipient.last_name]
        )
        notification.extra_payload['user_key'] = dispatch.recipient.uuid
        notification.extra_payload['current_site'] = get_base_url()
        resource = RESOURCE_MAPPING[notification.type.runtime_tag]
        send = partial(
            cls.send,
            dispatch=dispatch,
            notification=notification,
            resource=resource,
            recipient=dispatch.recipient,
        )
        is_by_email_success = True
        is_by_push_success = True

        logger.info(
            f'Dispatching notification: \n'
            f'Notification {notification.pk}\n'
            f'Notification tag {resource.runtime_tag}\n'
            f'Content object id {notification.object_id}\n'
            f'Content type {notification.content_type}\n'
            f'Content object {notification.content_object}\n'
            f'Extra payload:\n{pprint.pformat(notification.extra_payload)}'
        )
        if dispatch.by_email:
            is_by_email_success = send(method='by_email')
        if dispatch.by_push:
            is_by_push_success = send(method='by_push')

        if all((is_by_email_success, is_by_push_success)):
            dispatch.send()
            dispatch.save()

    @staticmethod
    def send(
        dispatch: models.NotificationDispatch,
        notification: models.Notification,
        resource: BaseNotificationResource,
        method: str,
        recipient: AppUser
    ) -> bool:
        """Send notification by chosen method."""
        send_map = {
            'by_email': {
                'title': resource.get_email_subject(
                    notification, recipient=recipient
                ),
                'get_content': resource.get_email_notification_content,
                'send_function': send_notification_by_email
            },
            'by_push': {
                'title': notification.title,
                'get_content': resource.get_push_notification_content,
                'send_function': send_notification_by_push
            }
        }
        get_content = send_map[method]['get_content']
        send_function = send_map[method]['send_function']
        title = send_map[method]['title']
        content = get_content(
            notification=notification,
            recipient=recipient
        )
        return send_function(
            recipient=recipient,
            title=title,
            content=content,
            dispatch=dispatch,
            notification=notification,
        )
