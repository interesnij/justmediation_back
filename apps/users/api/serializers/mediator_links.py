from rest_framework import serializers
from ....core.api.serializers import BaseSerializer
from ....users import models
from .fields import MediatorUniversityField


class MediatorUniversitySerializer(BaseSerializer):
    """Serializer for `University` model."""

    class Meta:
        model = models.MediatorUniversity
        fields = (
            'id', 'title'
        )


class MediatorEducationSerializer(BaseSerializer):
    """Serializer for `MediatorEducation` model."""
    university = MediatorUniversityField()

    class Meta:
        model = models.MediatorEducation
        fields = (
            'id',
            'year',
            'university',
        )

    def validate(self, attrs):
        """ Сохраните новый экземпляр "Университета", если данные прошли проверку. """
        attrs = super().validate(attrs)
        if 'university' in attrs and not attrs['university'].pk:
            attrs['university'].save()
        return attrs


class UpdateMediatorEducationSerializer(MediatorEducationSerializer):
    """ Предоставляет поле идентификатора для метода `put` или `patch`. """
    id = serializers.IntegerField()
