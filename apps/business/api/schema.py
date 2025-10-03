from drf_yasg.utils import no_body
from ...core.api.utils import define_swagger_auto_schema
from . import serializers, views
from .swagger import BillingItemPaginationInspector


define_swagger_auto_schema(
    api_view=views.MatterViewSet,
    method_name='send_referral',
    responses={
        200: serializers.MatterSerializer
    },
)

define_swagger_auto_schema(
    api_view=views.MatterViewSet,
    method_name='close',
    responses={
        200: serializers.MatterSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.MatterViewSet,
    method_name='accept_referral',
    request_body=no_body,
    responses={
        200: serializers.MatterSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.MatterViewSet,
    method_name='share_with',
    responses={
        200: serializers.MatterSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.BillingItemViewSet,
    method_name='list',
    paginator_inspectors=[BillingItemPaginationInspector]
)

define_swagger_auto_schema(
    api_view=views.InvoiceViewSet,
    method_name='open',
    responses={
        200: '',
    }
)

define_swagger_auto_schema(
    api_view=views.InvoiceViewSet,
    method_name='export',
    responses={
        200: 'File ready to be downloaded',
    }
)

define_swagger_auto_schema(
    api_view=views.StatisticsViewSet,
    method_name='export',
    query_serializer=serializers.BusinessStatsQueryParamsSerializer,
    responses={
        200: 'File ready to be downloaded',
    }
)
