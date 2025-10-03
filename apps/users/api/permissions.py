from django.conf import settings

from rest_framework import permissions


class IsMediatorHasActiveSubscription(permissions.BasePermission):
    """Permission which checks that user has access to paid resources

    Applied to these endpoints:

        * `/api/v1/users/mediators/current/ ` CurrentMediatorView
        * `/users/mediators/current/statistics/current/` StatisticsMediatorView
        * `/api/v1/business/leads/` LeadViewSet
        * `/api/v1/business/matters/` MatterViewSet
        * `/api/v1/business/billing-items/` BillingItemViewSet
        * `/api/v1/promotion/events/` EventViewSet
        * `/api/v1/business/invoices/` InvoiceViewSet
        * `/api/v1/business/activities/` ActivityViewSet
        * `/api/v1/business/notes/` NoteViewSet
        * `/api/v1/business/checklist/` ChecklistEntryViewSet
        * `/api/v1/business/stages/` StageViewSet
        * `/api/v1/esign/envelopes/` EnvelopeViewSet
        * `/api/v1/esign/profiles/current/` CurrentESignProfileView
        * `/api/v1/accounting/auth/` QuickBooksAuthorizationView

    """
    def has_permission(self, request, view):
        """ Проверьте, действительна ли подписка и является ли пользователь адвокатом """
        if not request.user.is_mediator:
            return False
        return False
        return request.user.has_active_subscription


class IsMediatorFreeAccess(permissions.BasePermission):
    """Permission which checks if request user is Mediator"""

    def has_permission(self, request, view):
        """Check if request user is Mediator"""
        return request.user.is_mediator

class IsEnterpriseAdmin(permissions.BasePermission):
    """Permission which checks if request user is Enterprise admin"""

    def has_permission(self, request, view):
        """Check if request user is Enterprise admin"""
        return request.user.is_enterprise_admin


class IsEnterpriseAdminOf(permissions.BasePermission):
    """Permission which checks if request user is admin
    of requested enterprise resource"""

    def has_permission(self, request, view):
        """Check if request user is admin of specified enterprise"""
        return request.user.is_enterprise_admin_of(view.kwargs.get('pk'))


class IsClient(permissions.BasePermission):
    """Permission which checks if request user is Client"""

    def has_permission(self, request, view):
        """Check if request user is Client"""
        return request.user.is_client


class IsSupport(permissions.BasePermission):
    """Permission which checks if request user is Support"""

    def has_permission(self, request, view):
        """Check if request user is Support"""
        return request.user.is_support


class CanUpdatePA(permissions.BasePermission):
    """Permission which checks if user can update PA list"""

    def has_permission(self, request, view):
        """Check if request user is Support"""
        return (
            request.user.is_staff or
            request.user.is_mediator
        )


class IsSupportPaidFee(permissions.BasePermission):
    """Permission which checks that support user paid fee."""

    def has_permission(self, request, view):
        """Check if user is support and paid subscription fee."""
        if not request.user.is_support:
            return False

        # Skip subscription permission for  local envs
        if settings.ENVIRONMENT == 'local' and not settings.STRIPE_ENABLED:
            return True

        return request.user.support.is_paid


class CanFollow(permissions.IsAuthenticated):
    """Permission which checks is user allowed to follow mediator.

    Checks if user isn't trying to follow itself.
    Checks if user is client.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user isn't trying to follow itself and it's not mediator"""
        return request.user != obj.user and request.user.is_client


class IsInviteOwner(IsMediatorFreeAccess):
    """Permission which checks if user is owner of invite."""

    def has_object_permission(self, request, view, obj):
        """Check if request user is owner of invite."""
        #return obj.inviter == request.user
        return True


class IsOwner(permissions.BasePermission):
    """Permission which checks if request user is owner
    of requested resource"""

    def has_permission(self, request, view):
        """Check if request user is owner of requested resource"""
        return str(request.user.id) == view.kwargs.get('pk')
