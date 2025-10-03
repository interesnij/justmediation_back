from rest_framework import generics, mixins, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ....core.api.views import BaseViewSet, UserAgentLoggingMixin
from ... import models
from ...api import filters, permissions, serializers


class SupportViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Endpoint for search support users and their registration."""
    serializer_class = serializers.SupportSerializer
    #queryset = models.Support.objects.all().verified().paid().select_related(
    #    'user'
    #)
    queryset = models.Support.objects.all()
    permissions_map = {
        'create': (AllowAny,)
    }
    filterset_class = filters.SupportFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
        'description',
    ]
    ordering_fields = [
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
        'description',
    ]
    # Explanation:
    #    We changed lookup_value_regex to avoid views sets urls collapsing
    #    for example when you have view set at `users` and at `users/mediator`,
    #    without it view set will collapse with at `users` in a way that
    #    users view set we use 'mediator' part of url as pk for search in
    #    retrieve method.
    lookup_value_regex = '[0-9]+'

    def create(self, request, *args, **kwargs):
        """Register user and return its support profile."""
        serializer = serializers.SupportRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(self.request)
        headers = self.get_success_headers(serializer.validated_data)
        serializer = serializers.SupportSerializer(instance=user.support)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class CurrentSupportView(
    UserAgentLoggingMixin,
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView,
):
    """Retrieve and update `support` user's profile.

    Accepts GET, PUT and PATCH methods.
    Read-only fields: user.
    """
    serializer_class = serializers.SupportSerializer
    permission_classes = IsAuthenticated, permissions.IsSupport

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests."""
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateSupportSerializer
        return super().get_serializer_class()

    def get_object(self):
        """Get support user's profile."""
        return self.request.user.support
