from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ....core.api.views import BaseViewSet
from ....users import models, utils
from ...api import permissions, serializers


class InviteViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """View set to work with `Invite` model."""
    invite_permissions = (IsAuthenticated, permissions.IsInviteOwner)
    permissions_map = {
        'retrieve': (AllowAny, ),
        'list': invite_permissions,
        #'create': invite_permissions,
        'create': (AllowAny, ),
        'update': invite_permissions,
        'partial_update': invite_permissions,
        'resend': invite_permissions,
    }
    serializer_class = serializers.InviteSerializer
    queryset = models.Invite.objects.without_user().only_invited_type()
    search_fields = (
        '@first_name',
        '@last_name',
        'email',
    )
    ordering_fields = (
        'sent',
        'email',
        'first_name',
        'last_name',
    )

    def get_queryset(self):
        """Filter invitations.

        If it is 'retrieve' action, return active invites.
        In others cases, return mediator's invites.

        """
        qs = super().get_queryset()
        if self.action == 'retrieve':
            return qs

        return qs.filter(inviter=self.request.user)

    @action(methods=['POST'], detail=True, url_path='resend')
    def resend(self, request, *args, **kwargs):
        """Resend invitation."""
        invite = self.get_object()
        utils.send_invitation(invite)
        return Response(status=status.HTTP_204_NO_CONTENT)
