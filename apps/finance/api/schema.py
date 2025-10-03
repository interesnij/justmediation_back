from drf_yasg.openapi import Response
from libs.api.serializers.serializers import URLSerializer
from ...core.api.utils import CALLBACKS_TAG, define_swagger_auto_schema
from . import serializers, views

define_swagger_auto_schema(
    api_view=views.AppUserPaymentSubscriptionView,
    method_name='get_setup_intent',
    responses={
        200: serializers.SetupIntentTokenSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.SubscriptionOptions,
    method_name='cancel_subscription',
    responses={
        200: serializers.SubscriptionSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.SubscriptionOptions,
    method_name='reactivate_subscription',
    responses={
        200: serializers.SubscriptionSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.SubscriptionOptions,
    method_name='preview_change_subscription',
    responses={
        200: serializers.SubscriptionSwitchPreviewSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.SubscriptionOptions,
    method_name='change_subscription',
    responses={
        200: serializers.SubscriptionSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.AccountAuthViewSet,
    method_name='get_authorization_link',
    query_serializer=None,
    responses={
        200: URLSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.AccountAuthViewSet,
    method_name='process_auth_callback',
    query_serializer=type(
        'StripeOAuthCallBackSerializer',
        (
            serializers.SuccessCallbackSerializer,
            serializers.ErrorCallbackSerializer
        ),
        {}
    ),
    responses={
        '302': Response(
            description='Redirect response by `success_url` or `error_url` '
            'taken from cache in `finance_deposits_auth_callback` operation.'
        ),
        '200': None
    },
    tags=[CALLBACKS_TAG]
)

define_swagger_auto_schema(
    api_view=views.CurrentAccountViewSet,
    method_name='get_login_link',
    responses={
        200: URLSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.CurrentAccountViewSet,
    method_name='get_onboarding_link',
    responses={
        200: URLSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.PaymentsViewSet,
    method_name='start_payment_process',
    responses={
        200: serializers.PaymentSerializer,
    }
)
