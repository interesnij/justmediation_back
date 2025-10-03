from django_filters import rest_framework as filters

from .. import models


class EnvelopeFilter(filters.FilterSet):
    """Filter by nested fields for Envelope model
    """

    class Meta:
        model = models.Envelope
        fields = {
            'id': ['exact', 'in'],
            'type': ['exact'],
            'matter': ['exact'],
        }
