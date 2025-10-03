from datetime import datetime

from rest_framework import serializers

from libs.api.serializers.fields import DateTimeFieldWithTimeZone

from apps.core.api.serializers import BaseSerializer

from ...promotion import models
from ...users.api.serializers import TimezoneSerializer


class EventSerializer(BaseSerializer):
    """Serializer for `Event` model."""

    timezone_data = TimezoneSerializer(
        source='timezone', read_only=True
    )

    class Meta:
        model = models.Event
        fields = (
            'id',
            'mediator',
            'title',
            'description',
            'is_all_day',
            'start',
            'end',
            'duration',
            'location',
            'timezone',
            'timezone_data'
        )
        read_only_fields = (
            'mediator',
            'duration',
        )

    def validate(self, attrs):
        """Set event's organiser(mediator)."""
        if self.user.is_mediator:
            attrs['mediator'] = self.user.mediator
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if '.' in data['start']:
            data['start'] = data['start'].split('.')[0] + 'Z'
        if '.' in data['end']:
            data['end'] = data['end'].split('.')[0] + 'Z'
        instance.start = datetime.strptime(
            data['start'], '%Y-%m-%dT%H:%M:%S%z'
        )
        instance.end = datetime.strptime(
            data['end'], '%Y-%m-%dT%H:%M:%S%z'
        )
        instance.save()
        return data


class EventShortSerializer(BaseSerializer):
    """Serializes events"""

    when = DateTimeFieldWithTimeZone(source='start')
    what = serializers.CharField(source='title')
    where = serializers.CharField(source='location')

    class Meta:
        model = models.Event
        fields = (
            'id',
            'when',
            'what',
            'where',
        )
        read_only_fields = fields
