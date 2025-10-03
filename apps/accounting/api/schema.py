from drf_yasg.openapi import Response
from libs.api.serializers.serializers import (
    SuccessErrorUrlRequestSerializer,
    URLSerializer,
)
from apps.core.api.utils import CALLBACKS_TAG, define_swagger_auto_schema
from . import serializers, views


define_swagger_auto_schema(
    api_view=views.QuickBooksAuthorizationView,
    method_name='get_authorization_url',
    query_serializer=SuccessErrorUrlRequestSerializer,
    responses={
        '200': URLSerializer
    }
)

define_swagger_auto_schema(
    api_view=views.QuickBooksAuthorizationView,
    method_name='process_auth_callback',
    query_serializer=type(
        'QuickBooksCallBackSerializer',
        (
            serializers.AccessAllowedSerializer,
            serializers.AccessDeniedSerializer
        ),
        {}
    ),
    responses={
        '302': Response(
            description='Redirect response by `success_url` or `error_url` '
            'taken from cache in `accounting_auth_get_authorization_url` '
            'operation.'
        ),
        '200': None
    },
    tags=[CALLBACKS_TAG]
)

define_swagger_auto_schema(
    api_view=views.QuickBooksExportView,
    method_name='export',
    query_serializer=serializers.ExportInvoiceSerializer,
    responses={
        '200': Response(description='Response with successful export status'),
        '201': None
    }
)
