import logging

from post_request_task.task import task

from config.celery import app

from ..core.models import BaseModel
from . import models, querysets
from .services.dispatcher import NotificationDispatcher

logger = logging.getLogger('django')


@task()
def send_notifications(resource_class, instance: BaseModel, **kwargs):
    """Send notifications by using notification resource and dispatcher."""
    resource = resource_class(instance=instance, **kwargs)
    notification = models.Notification.objects.create(
        type=resource.notification_type,
        title=resource.title,
        content_object=resource.instance,
        extra_payload=resource.get_notification_extra_payload(),
    )
    dispatcher = NotificationDispatcher(
        resource=resource,
        notification=notification
    )
    logger.info(
        f'Beginning notification sending process `{resource.runtime_tag}`'
    )
    dispatcher.notify()
    logger.info(
        f'Notification sending process has ended `{resource.runtime_tag}`'
    )


@app.task()
def resend_notifications(dispatches: querysets.NotificationDispatchQuery):
    """Resend notifications by using notification dispatches."""
    dispatcher = NotificationDispatcher(dispatches=dispatches)
    logger.info('Beginning notification re-sending process')
    dispatcher.notify()
    logger.info('Notification re-sending process has ended')
