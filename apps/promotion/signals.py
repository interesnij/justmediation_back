from django.db.models import signals
from django.dispatch import Signal, receiver

import arrow

from .models import Event

new_mediator_event = Signal(providing_args=('instance',))
new_mediator_event.__doc__ = (
    'Signal that indicates that there is a new mediator event'
)


@receiver(signals.pre_save, sender=Event)
def all_day_event(instance: Event, **kwargs):
    """Set for all day event start 00:00 and end 23:59."""
    if instance.is_all_day:
        arrow_date = arrow.get(instance.start)
        instance.start = arrow_date.floor('day').datetime
        instance.end = arrow_date.ceil('day').datetime


@receiver(signals.post_save, sender=Event)
def new_event(instance: Event, created: bool, **kwargs):
    """Send signal that mediator created new event."""
    if not created:
        return

    new_mediator_event.send(sender=Event, instance=instance)
