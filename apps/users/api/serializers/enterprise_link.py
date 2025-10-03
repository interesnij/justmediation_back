from ....core.api.serializers import BaseSerializer
from ....users import models


class MemberSerializer(BaseSerializer):
    """ Serializer for Member of Enterprise """

    class Meta:
        model = models.Member
        fields = (
            'email',
        )
