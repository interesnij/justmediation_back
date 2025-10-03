from rest_framework import permissions


class IsEventOrganizer(permissions.IsAuthenticated):
    """Permission which checks ownership of event."""

    def has_object_permission(self, request, view, obj):
        """Check if request user has ownership on event."""
        return request.user == obj.mediator.user | request.user.is_mediator
