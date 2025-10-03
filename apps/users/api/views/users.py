from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from apps.core.api.views import ReadOnlyViewSet
from ... import utils
from ...models import AppUser
from ..filters import AppUserFilter
from ..serializers import (
    AppUserSerializer,
    AppUserTwoFASerializer,
    PhoneSerializer,
    TwoFASerializer,
)


class AppUserViewSet(ReadOnlyViewSet):
    """Separate viewset to get all app users with different filtration params.
    """
    lookup_value_regex = '[0-9]+'
    permissions_map = {
        'default': (IsAuthenticated,),
        'is_registered': (AllowAny,),
        'is_twofa': (AllowAny,),
        'unsubsribe': (AllowAny,),
        'send_code': (AllowAny,),
    }
    permission_classes = (
        IsAuthenticated,
    )
    serializer_class = AppUserSerializer
    queryset = AppUser.objects.all().active().exclude_staff().select_related(
        'forum_stats',
        'mediator',
        'client',
    ).prefetch_related(
        'specialities',
    )
    filterset_class = AppUserFilter
    search_fields = [
        '@first_name',
        '@last_name',
        'email',
    ]
    ordering_fields = [
        'email',
        'first_name',
        'last_name',
    ]

    @action(methods=['get'], detail=False, url_path='is-registered')
    def is_registered(self, request):
        """Check new email addresss if it is registerd in db"""
        qp = self.request.query_params
        if AppUser.objects.is_registered(qp.get('email')):
            return Response(
                data={'is_registered': True},
                status=status.HTTP_200_OK)
        else:
            return Response(
                data={'is_registered': False},
                status=status.HTTP_200_OK
            )

    @action(methods=['post'], detail=False, url_path='unsubscribe')
    def unsubsribe(self, request, *args, **kwargs):
        """Unsubsribe email notification"""
        key = request.data.get('key', None)
        try:
            user = AppUser.objects.get(uuid=key)
            user.is_subscribed = False
            user.save()
            return Response(
                data={'success': True},
                status=status.HTTP_200_OK
            )
        except ValidationError:
            return Response(
                data={'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AppUser.DoesNotExist:
            return Response(
                data={'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def twofa(self, request, *args, **kwargs):
        """Update 2-Factor Authentication flag"""
        user = self.get_object()
        serializer = TwoFASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.phone is None:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': 'Can not set 2FA, because your number is empty'
                }
            )
        user.twofa = serializer.validated_data['twofa']
        user.save()
        return Response(
            status=status.HTTP_200_OK,
            data=AppUserSerializer(instance=user).data
        )

    @action(detail=False, methods=['get'])
    def is_twofa(self, request, *args, **kwargs):
        """Get 2-Factor Authentication flag"""
        qp = self.request.query_params
        try:
            user = AppUser.objects.get(email__iexact=qp.get('email').strip())
            return Response(
                status=status.HTTP_200_OK,
                data=AppUserTwoFASerializer(instance=user).data
            )
        except AppUser.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "detail": "User does not exist with this email"
                }
            )

    @action(detail=False, methods=['post'])
    def send_code(self, request, *args, **kwargs):
        """Send 2-Factor code via sms"""
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = utils.format_phone_for_twillio(data.get('phone', None))
        try:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            service = settings.TWILIO_SERVICE
            client = Client(account_sid, auth_token)

            verification = client.verify.services(service).verifications.\
                create(to=phone, channel='sms')
            if verification:
                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        'detail': 'Sent code successfully'
                    }
                )
        except TwilioRestException as e:
            if e.status == 429:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'code': e.code,
                        'status': e.status,
                        'detail': 'Max send attempts reached, please try later'
                    }
                )
            else:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'code': e.code,
                        'status': e.status,
                        'detail': str(e)
                    }
                )
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': str(e)
                }
            )
