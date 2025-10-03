from apps.core.api.utils import CALLBACKS_TAG, define_swagger_auto_schema

from . import serializers, views

define_swagger_auto_schema(
    api_view=views.EnvelopeViewSet,
    method_name='create',
    query_serializer=serializers.RequiredReturnURLSerializer,
)

define_swagger_auto_schema(
    api_view=views.EnvelopeViewSet,
    method_name='retrieve',
    query_serializer=serializers.RequiredReturnURLSerializer,
    responses={'200': serializers.EnvelopeSerializer}
)

define_swagger_auto_schema(
    api_view=views.CurrentESignProfileView,
    method_name='get',
    query_serializer=serializers.ReturnURLSerializer,
    responses={'200': serializers.ESignProfileSerializer}
)

define_swagger_auto_schema(
    api_view=views.ESignCallbacksView,
    method_name='save_consent',
    query_serializer=serializers.SaveUserConsentSerializer,
    responses={
        '302': 'Redirect to DocuSign',
        '400': 'Invalid data',
        '200': None  # set to None for swagger docs
    },
    tags=[CALLBACKS_TAG])

define_swagger_auto_schema(
    api_view=views.ESignCallbacksView,
    method_name='update_envelope_status',
    responses={
        '204': 'Envelop status updated',
    },
    tags=[CALLBACKS_TAG]
)
