from drf_yasg.utils import no_body

from ...core.api.utils import define_swagger_auto_schema
from . import serializers, views

define_swagger_auto_schema(
    api_view=views.SupportViewSet,
    method_name='create',
    request_body=serializers.SupportRegisterSerializer,
    responses={
        201: serializers.SupportSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.ClientViewSet,
    method_name='create',
    request_body=serializers.ClientRegisterSerializer,
    responses={
        201: serializers.ClientSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.AppUserViewSet,
    method_name='twofa',
    request_body=serializers.TwoFASerializer,
    responses={
        200: serializers.AppUserSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.AppUserViewSet,
    method_name='is_twofa',
    request_body=None,
    responses={
        200: serializers.TwoFASerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.AppUserViewSet,
    method_name='send_code',
    request_body=serializers.PhoneSerializer,
    responses={
        200: None,
    }
)

define_swagger_auto_schema(
    api_view=views.MediatorViewSet,
    method_name='create',
    request_body=serializers.MediatorRegisterSerializer,
    responses={
        201: serializers.MediatorSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.MediatorViewSet,
    method_name='follow',
    request_body=no_body,
    responses={
        204: 'Mediator followed',
    }
)

define_swagger_auto_schema(
    api_view=views.MediatorViewSet,
    method_name='unfollow',
    request_body=no_body,
    responses={
        204: 'Mediator unfollowed',
    }
)

define_swagger_auto_schema(
    api_view=views.InviteViewSet,
    method_name='resend',
    request_body=no_body,
    responses={
        204: 'Invitation was resent',
    }
)

define_swagger_auto_schema(
    api_view=views.MediatorViewSet,
    method_name='validate_registration',
    query_serializer=serializers.MediatorRegisterValidateSerializer,
    responses={
        204: 'Registration data is valid',
        400: 'Invalid registration data',
    }
)

define_swagger_auto_schema(
    api_view=views.CurrentMediatorActionsViewSet,
    method_name='current_statistics',
    responses={
        200: serializers.MediatorCurrentStatisticsDataSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.CurrentMediatorActionsViewSet,
    method_name='period_statistics',
    responses={
        200: serializers.MediatorPeriodStatisticsDataSerializer,
    },
    query_serializer=serializers.MediatorPeriodStatsQueryParamsSerializer
)

define_swagger_auto_schema(
    api_view=views.AppUserLoginView,
    method_name='post',
    request_body=serializers.AppUserLoginSerializer,
    responses={
        200: serializers.TokenSerializer,
    }
)

define_swagger_auto_schema(
    api_view=views.ValidateCredentialView,
    method_name='post',
    request_body=serializers.AppUserLoginValidationSerializer,
    responses={
        200: None,
    }
)
