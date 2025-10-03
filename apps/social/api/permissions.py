from rest_framework.permissions import BasePermission


class IsChatParticipant(BasePermission):
    """Check if user is a group chat participant."""

    def has_object_permission(self, request, view, obj):
        return obj.is_participant(request.user)


class IsMediatorPostAuthor(BasePermission):
    """Check if user is author of mediator post."""

    def has_object_permission(self, request, view, obj):
        return request.user.pk == obj.author_id
