from rest_framework import mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.users.api import filters

from ....core.api.views import BaseViewSet
from ...api import serializers
from ...models import (
    AppointmentType,
    Currencies,
    FeeKind,
    LawFirm,
    FirmSize,
    Language,
    PaymentType,
    Speciality,
    TimeZone,
)
from ..permissions import CanUpdatePA


class SpecialityViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    BaseViewSet
):
    """Api view to list all specialities."""
    serializer_class = serializers.SpecialitySerializer
    base_permission_classes = (AllowAny,)
    permissions_map = {
        "create": (IsAuthenticated, CanUpdatePA, ),
        "update": (IsAuthenticated, CanUpdatePA, ),
    }
    queryset = Speciality.objects.order_by('title')
    search_fields = [
        'title',
    ]
    filterset_class = filters.SpecialityFilter

    def list(self, request, *args, **kwargs):
        self.pagination_class.default_limit = 1000
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.created_by == request.user:
            return super().update(request, *args, **kwargs)
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': 'You can not edit this PA'
                }
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.created_by == request.user:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': 'You can not delete this PA'
                }
            )


class FeeKindViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all fee kinds."""
    serializer_class = serializers.FeeKindSerializer
    base_permission_classes = (AllowAny,)
    queryset = FeeKind.objects.all()
    search_fields = [
        'title',
    ]

class LawFirmViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all fee kinds."""
    serializer_class = serializers.LawFirmSerializer
    base_permission_classes = (AllowAny,)
    queryset = LawFirm.objects.all()
    search_fields = [
        'name',
    ]
    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        search = qp.get('search', None)
        if search == '':
            print("search!!")
            return qs.filter(name="1000000000")
        if search:
            from django.db.models import Q
            return qs.filter(
                Q(name__icontains=search)
            )
        return qs.filter(name="1000000000")

class AppointmentTypeViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all appointment types."""
    serializer_class = serializers.AppointmentTypeSerializer
    base_permission_classes = (AllowAny,)
    queryset = AppointmentType.objects.all()
    search_fields = [
        'title',
    ]


class PaymentTypeViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all payment methods."""
    serializer_class = serializers.PaymentTypeSerializer
    base_permission_classes = (AllowAny,)
    queryset = PaymentType.objects.all()
    search_fields = [
        'title',
    ]


class LanguageViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all languages."""
    serializer_class = serializers.LanguageSerializer
    base_permission_classes = (AllowAny,)
    queryset = Language.objects.order_by('title')
    search_fields = [
        'title',
    ]


class CurrenciesViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all curriences."""
    serializer_class = serializers.CurrenciesSerializer
    base_permission_classes = (AllowAny,)
    queryset = Currencies.objects.all()
    search_fields = [
        'title',
    ]


class FirmSizeViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all firm size values"""
    serializer_class = serializers.FirmSizeSerializer
    base_permission_classes = (AllowAny,)
    queryset = FirmSize.objects.all()
    search_fields = [
        'title',
    ]


class TimezoneViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all timezone values"""
    serializer_class = serializers.TimezoneSerializer
    base_permission_classes = (AllowAny,)
    queryset = TimeZone.objects.all()
    search_fields = [
        'title',
    ]
