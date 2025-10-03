from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import pytz

from apps.core.models import BaseModel


class EventsQuerySet(QuerySet):
    """QuerySet class for Events model. """

    def upcoming(self):
        """Filter upcoming events(events that are going to happen)."""
        present = timezone.now()
        return self.filter(
            Q(start__gt=present) |
            Q(is_all_day=True, end__gt=present)
        )


class Event(BaseModel):
    """Model defines mediator's events.

    mediators can organize simple events and display them to clients.

    Attributes:
        mediator (mediator): Link to event organizer.
        title (str): Title of event.
        start (datetime): When event starts.
        end (datetime): When event ends.
        is_all_day (bool):
            Is event all day. All day event is event, that goes from 00:00 am
            to 23:59 pm.
        location (str): Where event will take place.
        timezone (Timezone): timezone of event
        description(str): Description of event.

    """

    mediator = models.ForeignKey(
        'users.Mediator',
        on_delete=models.PROTECT,
        related_name='events',
        null=True,
        default=None
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title of event'),
    )

    start = models.DateTimeField(
        verbose_name=_('Start of event')
    )

    end = models.DateTimeField(
        verbose_name=_('End of event')
    )

    is_all_day = models.BooleanField(
        default=False,
        verbose_name=_('Is event is all day'),
        help_text=_('Indicates if event is all day or not')
    )

    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Location'),
        help_text=_('Location of event'),
    )

    timezone = models.ForeignKey(
        'users.Timezone',
        on_delete=models.PROTECT,
        related_name='events',
        null=True,
        blank=True,
        default=None
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of event'),
    )

    objects = EventsQuerySet.as_manager()

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        constraints = [
            models.CheckConstraint(
                check=models.Q(start__lt=models.F('end')),
                name='start must be earlier then end'
            ),
        ]

    def __str__(self):
        return self.title

    def clean_start(self):
        """Validate start date.

        Check that start date is earlier than end of event.
        Check that start day end day must match if event is all day

        """
        if self.start >= self.end:
            raise ValidationError(
                _(
                    "Enter valid 'start' and 'end' dates and times"
                    "('end' is earlier that 'start'(start > end error))"
                )
            )

        # if self.is_all_day:
        #     if self.start.day != self.end.day:
        #         raise ValidationError(_("Date can't be in past"))

    def clean_end(self):
        """Check that end date is not in past."""

        if self.end <= timezone.now():
            raise ValidationError(_("Date can't be in past"))

    def save(self, **kwargs):
        """Set timezones for event dates to UTC.

        When django saves datetime objects in converts them to the UTC
        timezone, for events we want to avoid it. So we set UTC timezone
        for dates without conversation.

        """
        timezone = pytz.timezone(self.timezone.title)
        self.start = self.start.replace(tzinfo=pytz.utc).astimezone(timezone)
        self.end = self.end.replace(tzinfo=pytz.utc).astimezone(timezone)
        super().save(**kwargs)

    @property
    def duration(self):
        """Get duration of event."""
        if self.end and self.start:
            return self.end - self.start
