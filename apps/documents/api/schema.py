from ...core.api.utils import define_swagger_auto_schema
from . import serializers, views


define_swagger_auto_schema(
    api_view=views.ResourcesView,
    method_name='list',
    responses={
        200: serializers.CommonResourceSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.DocumentViewSet,
    method_name='duplicate',
    responses={
        201: serializers.DocumentSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.FolderViewSet,
    method_name='duplicate',
    responses={
        201: serializers.FolderSerializer
    }
)
