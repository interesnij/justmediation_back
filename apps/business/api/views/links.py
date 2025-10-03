import logging
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_condition import And, Or
from ....core.api import views
from ....users.api.permissions import (
    IsMediatorHasActiveSubscription,
    IsClient,
    IsSupportPaidFee,
)
from ... import models
from .. import filters, serializers
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class ActivityViewSet(BusinessViewSetMixin, views.ReadOnlyViewSet):
    """ Представление api только для чтения, установленное для модели `Activity`. """
    queryset = models.Activity.objects.all().select_related(
        'matter',
        'user',
    )
    serializer_class = serializers.ActivitySerializer
    filterset_class = filters.ActivityFilter
    search_fields = (
        'title',
        'matter__title',
        'matter__code',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'title',
        'matter__title',
    )


class VoiceConsentViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    views.ReadOnlyViewSet
):
    """ Представление api модели `VoiceConsent`.

    Голосовые согласия доступны для прочтения всем пользователям - адвокатам,
    клиентам, общим адвокатам и службе поддержки. Только клиенты могут создавать голосовые сообщения
    соглашается. Только адвокаты, совместные адвокаты и служба поддержки могут устранить проблему
    выражают согласие по доступным для них вопросам.

    """
    queryset = models.VoiceConsent.objects.all().prefetch_related('matter')
    serializer_class = serializers.VoiceConsentSerializer
    default_permissions = [And(
        IsAuthenticated(),
        (Or(
            IsMediatorHasActiveSubscription(),
            IsClient(),
            IsSupportPaidFee()
        ))
    )]
    permissions_map = {
        'default': default_permissions,
        'create': BusinessViewSetMixin.client_permissions,
        'destroy': (BusinessViewSetMixin.mediator_support_permissions,),
    }
    filterset_class = filters.VoiceConsentFilter
    ordering_fields = (
        'created',
        'modified',
    )


class NoteViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """ Представление CRUD api модели `Note`."""
    queryset = models.Note.objects.all().select_related(
        'matter',
        'matter__referral__mediator__user',
        'matter__mediator__user',
        'matter__client__user',
        'client',
        'created_by'
    ).prefetch_related(
        'attachments'
    )
    serializer_class = serializers.NoteSerializer
    serializers_map = {
        'update': serializers.UpdateNoteSerializer,
        'partial_update': serializers.UpdateNoteSerializer,
    }
    # заметки могут быть созданы, обновлены и удалены "клиентом", `адвокатом`
    # с активной подпиской или поддержкой, оплатившей абонентскую плату
    user_permissions = [And(
        IsAuthenticated(),
        (Or(
            IsMediatorHasActiveSubscription(),
            IsClient(),
            IsSupportPaidFee()
        ))
    )]
    permissions_map = {
        'create': user_permissions,
        'update': user_permissions,
        'partial_update': user_permissions,
        'destroy': user_permissions,
    }
    filterset_class = filters.NoteFilter
    search_fields = (
        'title',
        'matter__title',
    )
    ordering_fields = (
        'id',
        'title',
        'matter',
        'created',
        'modified',
    )

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        print(qs)
        return qs.exclude(
            matter__status=models.Matter.STATUS_REFERRAL,
            matter__referral__mediator__user=user
        )


class MatterSharedWithViewSet(BusinessViewSetMixin, views.ReadOnlyViewSet):
    """ Представление api только для чтения, установленное для модели `MatterSharedWith`.

    Используется интерфейсом для получения информации о matter для `new_matter_shared`
    уведомление.

    """
    queryset = models.MatterSharedWith.objects.all().select_related(
        'matter',
        'user'
    )
    serializer_class = serializers.MatterSharedWithSerializer
    filterset_class = filters.MatterSharedWithFilter
    search_fields = (
        'matter__title',
        'matter__code',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'matter__title',
    )
