from ...core.api.utils import define_swagger_auto_schema
from . import serializers, views

define_swagger_auto_schema(
    api_view=views.ChatViewSet,
    method_name='messages',
    responses={
        200: serializers.MessageSerializer
    },
)
