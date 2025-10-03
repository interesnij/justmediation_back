from django.db.models import BooleanField, Case, When
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django_fsm import TransitionNotAllowed
from libs.django_fcm.api.exceptions import WrongTransitionException
from apps.core.api.views import (
    BaseGenericViewSet,
    ReadOnlyViewSet,
    UserAgentLoggingMixin,
)
from ...notifications import models
from ..api import filters, pagination, serializers


class NotificationSettingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    UserAgentLoggingMixin,
    GenericViewSet,
):
    """View set to work with all current users' notifications' settings."""
    serializer_class = serializers.NotificationSettingSerializer
    queryset = models.NotificationSetting.objects.all()
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        notification, _ = models.NotificationSetting.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Create or update notification settings.

        `Create` if there are no settings for input `notification_type`.
        `Update` if settings for input `notification_type` exist

        """
        serializer = serializers.NotificationSettingSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        default = {}
        for item in data.items():
            default['by_'+item[0]] = item[1]
        notification, _ = models.NotificationSetting.objects.update_or_create(
            user=self.request.user,
            defaults=default
        )
        serializer = serializers.NotificationSettingSerializer(
            instance=notification
        )
        return Response(serializer.data, status=status.HTTP_200_OK,)


class NotificationDispatchViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseGenericViewSet,
):
    """View set to work with all current users notifications dispatches.

    Notifications dispatches are user's actual `notifications` with it's
    current state(if it is read or not), which were pushed to user.

    """
    serializer_class = serializers.NotificationDispatchSerializer
    pagination_class = pagination.NotificationLimitOffsetPagination
    serializers_map = {
        'read': None,
        'unread': None,
    }
    queryset = models.NotificationDispatch.objects.all().select_related(
        'sender',
        'notification',
        'notification__type',
        'notification__type__group',
        'notification__content_type',
    ).prefetch_related(
        'notification__content_object',
    )
    filterset_class = filters.NotificationDispatchFilter
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """Limit returned dispatches to current user."""
        qs = super().get_queryset()
        return qs.filter(recipient=self.request.user).annotate(
            is_read=Case(
                When(
                    status=models.NotificationDispatch.STATUS_READ, then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).order_by('is_read', '-modified')

    @action(methods=['post'], detail=True, url_path='read')
    def read(self, request, **kwargs):
        """Mark notification as 'read'."""
        dispatch = self.get_object()
        try:
            dispatch.read()
            dispatch.save()
        except TransitionNotAllowed:
            raise WrongTransitionException
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unread')
    def unread(self, request, **kwargs):
        """Mark notification as 'unread'."""
        dispatch = self.get_object()
        try:
            dispatch.unread()
            dispatch.save()
        except TransitionNotAllowed:
            raise WrongTransitionException
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationGroupViewSet(ReadOnlyViewSet):
    """View set to list all notification groups."""
    serializer_class = serializers.NotificationGroupSerializer
    queryset = models.NotificationGroup.objects.all().prefetch_related(
        'types'
    )
    filterset_class = filters.NotificationGroupFilter
    search_fields = (
        'title',
    )


class NotificationTypeViewSet(ReadOnlyViewSet):
    """View set to list all notification types."""
    serializer_class = serializers.NotificationTypeSerializer
    queryset = models.NotificationType.objects.all().select_related('group')
    filterset_class = filters.NotificationTypeFilter
    search_fields = (
        'title',
    )

    def get_queryset(self):
        """Return available for current user notification types."""
        qs = super().get_queryset()
        return qs.user_types(user=self.request.user)
