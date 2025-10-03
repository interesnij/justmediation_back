import logging
from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.db.models import signals as db_signals
from django.db.transaction import on_commit

from . import models, tasks
from .services.resources import RESOURCE_MAPPING

logger = logging.getLogger('django')


def generate_and_send_notification(instance, resource_class, **kwargs):
    """Generate notification for new event and send it to it's recipients."""
    logger.info(f'New notification: {resource_class.runtime_tag}')
    # Celery can't pickle signal object(_thread.lock object)
    kwargs.pop('signal')
    on_commit(
        lambda: tasks.send_notifications.delay(
            resource_class,
            instance,
            **kwargs
        )
    )


def delete_redundant_notification(instance, **kwargs):
    """Delete notifications without content object.

    This needed for this kind of scenarios: for example mediator made a post
    in topic, we create notification with a link to the post. But later
    mediator deletes post, and we have no way of getting content_object and
    because of that we can't generate notification message and show it to user.
    So there is nothing to do, but to delete redundant notifications with link
    to deleted object.

    """
    content_type = ContentType.objects.get_for_model(instance)
    models.Notification.objects.filter(
        content_type=content_type, object_id=instance.pk
    ).delete()


# Connect `generate_and_send_notification` function to all signal and model
# pairs from `SIGNALS_MAPPING`
# Connect all models from `SIGNALS_MAPPING` to `delete_redundant_notification`
for resource in RESOURCE_MAPPING.values():
    resource.signal.connect(
        receiver=partial(
            generate_and_send_notification,
            resource_class=resource
        ),
        sender=resource.instance_type,
        weak=False,
    )
    db_signals.post_delete.connect(
        receiver=delete_redundant_notification,
        sender=resource.instance_type,
    )
