from django.db.models import signals
from django.dispatch import Signal, receiver

from ..models import MatterComment
from ..services import (
    set_matter_post_comment_count,
    set_matter_post_last_comment,
)

new_message = Signal(providing_args=('instance',))
new_message.__doc__ = (
    'Signal that indicates that mediator or client left new message'
)


@receiver(signals.post_save, sender=MatterComment)
def update_topic_statistic(instance: MatterComment, created: bool, **kwargs):
    """Update matter topic instance on post creation."""
    if not created:
        return

    set_matter_post_comment_count(instance.post, 1)
    set_matter_post_last_comment(instance.post, instance)


@receiver(signals.post_save, sender=MatterComment)
def new_matter_message(instance: MatterComment, created: bool, **kwargs):
    """Send signal that there is new message for client or mediator."""
    if not created:
        return
