from rest_framework import mixins
from rest_framework.filters import SearchFilter
# from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_tracking.mixins import LoggingMixin

from libs.api.pagination import PageLimitOffsetPagination
from libs.api.views import mixins as core_mixins
from libs.sentry.api.views import SentryMixin

from apps.core.filters import CustomOrderingFilter


class UserAgentLoggingMixin(LoggingMixin):
    def handle_log(self):
        self.log['host'] = self.request.META.get("HTTP_USER_AGENT", "")
        super().handle_log()


class BaseViewSet(
    SentryMixin,
    core_mixins.ActionPermissionsMixin,
    core_mixins.ActionSerializerMixin,
    UserAgentLoggingMixin,
    GenericViewSet
):
    """Base viewset for api."""
    pagination_class = PageLimitOffsetPagination
    base_permission_classes = (IsAuthenticated,)
    base_filter_backends = (
        DjangoFilterBackend,
        CustomOrderingFilter,
        SearchFilter,
    )
    extra_filter_backends = None

    def get_viewset_permissions(self):
        """Custom method to prepare viewset permissions

        Method returns union of `base_permission_classes` and
        `permission_classes`, specified in child classes.

        """
        extra_permissions = tuple(
            permission for permission in self.permission_classes
            if permission not in self.base_permission_classes
        )
        permissions = self.base_permission_classes + extra_permissions
        return [permission() for permission in permissions]

    def get_filter_backends(self):
        """Allow to join ``base_filter_backends`` and
        ``extra_filter_backends`` and can be overridden in order.
        """
        base_backends = tuple(self.base_filter_backends or ())
        extra_backends = tuple(self.extra_filter_backends or ())
        return base_backends + extra_backends

    @property
    def filter_backends(self):
        """Allow to dynamically return filter backends."""
        return self.get_filter_backends()


class BaseGenericViewSet(BaseViewSet, GenericViewSet):
    """Base generic viewset for api views."""


class CRUDViewSet(
    BaseViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    """CRUD viewset for api views."""


class ReadOnlyViewSet(
    BaseViewSet,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """Read only viewset for api views."""
