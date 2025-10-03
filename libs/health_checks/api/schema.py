from apps.core.api.utils import define_swagger_auto_schema
from . import serializers, views


define_swagger_auto_schema(
    api_view=views.HealthCheckView,
    method_name='get',
    query_serializer=serializers.HealthCheckQuery,
    responses={200: serializers.HealthCheckResults},
)
