import logging

from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from constance import config

from apps.core.api.views import BaseViewSet, UserAgentLoggingMixin
from apps.users.api.permissions import IsMediatorHasActiveSubscription

from ..adapters import DocuSignAdapter
from ..models import Envelope, ESignProfile
from . import filters, serializers
from .utils import DocuSignXMLParser

logger = logging.getLogger('docusign')


def get_return_url(request, is_required: bool = True) -> str:
    """Shortcut to get `return_url` from request query data.

    Check request `query_data` for `return_url` param. By `is_required` flag
    we can omit error raising in case of absent `return_url` field.

    """
    serializer_class = serializers.RequiredReturnURLSerializer if is_required \
        else serializers.ReturnURLSerializer
    query_serializer = serializer_class(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)
    return query_serializer.validated_data.get('return_url', '')


class EnvelopeViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """API endpoint to work with esign envelopes.

    API provides only possibility to create new Envelope and get its edit link.

    """
    serializer_class = serializers.EnvelopeShortSerializer
    queryset = Envelope.objects.all().prefetch_related('documents')
    filterset_class = filters.EnvelopeFilter
    permission_classes = IsAuthenticated, IsMediatorHasActiveSubscription
    serializers_map = {
        'retrieve': serializers.EnvelopeSerializer,
        'list': serializers.EnvelopeShortSerializer,
        'create': serializers.EnvelopeSerializer,
    }

    def get_queryset(self):
        """Return only available for Mediator envelopes."""
        qs = super().get_queryset()
        return qs.available_for_user(self.request.user)

    def get_serializer_context(self):
        """Add DocuSign adapter to serializer context where it's needed.

        It is not required only in `list` action, cause we don't need DocuSign
        interactions there.

        """
        context = super().get_serializer_context()
        if self.action != 'list':
            context['adapter'] = DocuSignAdapter(self.request.user)
            # create and edit actions both should have `return_url` query param
            context['return_url'] = get_return_url(self.request)
        return context

    def create(self, request, *args, **kwargs):
        """Method to create new Envelope and get its edit link."""
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Overridden method to add query serializer swagger spec."""
        return super().retrieve(request, *args, **kwargs)


class CurrentESignProfileView(
    UserAgentLoggingMixin,
    generics.RetrieveAPIView,
    generics.DestroyAPIView,
    generics.GenericAPIView
):
    """Work with current user ESign profile.

    API allows to retrieve current user profile or delete it if it is needed.

    """
    serializer_class = serializers.ESignProfileSerializer
    permission_classes = IsAuthenticated, IsMediatorHasActiveSubscription

    def get_object(self):
        """Get user's esign profile or create a new one."""
        user = self.request.user
        esign_profile = getattr(user, 'esign_profile', None)
        if not esign_profile:
            esign_profile, _ = ESignProfile.objects.get_or_create(user=user)
        return esign_profile

    def get_serializer_context(self):
        """Define `return_url` on serializer level."""
        context = super().get_serializer_context()
        context['return_url'] = get_return_url(self.request, is_required=False)
        return context

    def get(self, request, *args, **kwargs):
        """Overridden method to set query params swagger spec."""
        return self.retrieve(request, *args, **kwargs)


class ESignCallbacksView(UserAgentLoggingMixin, GenericViewSet):
    """API View to process all related to esign callbacks from DocuSign."""
    pagination_class = None
    permission_classes = AllowAny,
    # add a separate `DocuSignXMLParser` for `update_envelope_status` callback
    parser_classes = [DocuSignXMLParser, JSONParser]

    @action(methods=['GET'], detail=False, url_path='save-consent')
    def save_consent(self, request, *args, **kwargs):
        """API method to save user consent for esigning.

        Method is called by DocuSign after obtaining consent. It updates
        corresponding user `docusign_id` in ESignProfile.

        """
        serializer = serializers.SaveUserConsentSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)

        # get impersonated user for DocuSignAdapter by callback `state`
        impersonated = ESignProfile.objects.all().get_profile_by_consent_id(
            consent_id=serializer.validated_data['state']
        )
        if not impersonated:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        adapter = DocuSignAdapter(user=impersonated.user)
        is_consent_obtained = not(
            'error' in request.query_params or
            'error_message' in request.query_params
        )
        # user agreed on consent - save it
        if is_consent_obtained:
            adapter.save_consent(**serializer.validated_data)
        # user canceled consent obtaining - do nothing and redirect user
        else:
            logger.debug(f'User {impersonated.pk} denied consent obtaining')

        # after consent is processed -> redirect user to corresponding url
        return_url = adapter.esign_profile.return_url or \
            config.BASE_OBTAIN_CONSENT_REDIRECT_URL
        return Response(
            headers={'Location': return_url},
            status=status.HTTP_302_FOUND
        )

    @action(methods=['POST'], detail=False, url_path='update-envelope-status')
    def update_envelope_status(self, request, *args, **kwargs):
        """API method triggered by DocuSign on Envelope `status` updates.
        """
        serializer = serializers.UpdateEnvelopeStatusSerializer(
            data=request.data.get('EnvelopeStatus')
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.warning(
                f"DocuSign callback couldn't update envelope status: {e}"
            )
            raise e
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
