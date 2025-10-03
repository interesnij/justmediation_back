import logging
from rest_framework import mixins, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_condition import And, Or
from ....core.api import views
from ....users.api.permissions import (
    IsMediatorHasActiveSubscription,
    IsClient,
    IsSupportPaidFee,
)
from ... import models, signals
from .. import filters, serializers
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class VideoCallViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    views.BaseViewSet
):
    """ Набор представлений API для модели `VideoCall`.
    Обеспечьте действия по созданию, извлечению и перечислению.
    """
    queryset = models.VideoCall.objects.all().prefetch_related(
        'participants'
    )
    serializer_class = serializers.VideoCallSerializer
    filterset_class = filters.VideoCallFilter
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
    }
    ordering_fields = (
        'created',
        'modified',
    )

    def create(self, request, *args, **kwargs):
        """ Создайте видеозвонок.
        Сначала мы проверяем, создан ли уже видеозвонок с пользователем и
        участниками, если нет, мы создаем новую запись о видеозвонке.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        # Извлеките данные, которые будут установлены после создания видеовызова
        participants = set(serializer.validated_data['participants'])
        participants.add(user.pk)

        video_call = models.VideoCall.objects.get_by_participants(
            participants
        )

        if not video_call:
            video_call = models.VideoCall.objects.create()
            video_call.participants.set(participants)

        signals.new_video_call.send(
            instance=video_call,
            caller=user,
            sender=models.VideoCall,
            user=user
        )

        serializer.instance = video_call
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class BaseMediatorRelatedViewSet(views.CRUDViewSet):
    """BaseCRUDview установлен для данных, связанных с адвокатом 
    (CRUD).
    """

    # чтение разрешено адвокатам или пользователям службы поддержки
    permission_classes = (BusinessViewSetMixin.mediator_support_permissions,)

    #  CRUD разрешено только адвокатам с активными подписками
    permissions_map = {
        'create': BusinessViewSetMixin.mediator_permissions,
        'update': BusinessViewSetMixin.mediator_permissions,
        'partial_update': BusinessViewSetMixin.mediator_permissions,
        'destroy': BusinessViewSetMixin.mediator_permissions,
    }

    def get_matter(self, user):
        """ получение доступного для пользователя `matter` из параметров запроса. """
        matter_id = self.request.query_params.get('matter')
        matter = get_object_or_404(
            models.Matter.objects.all().available_for_user(user),
            id=matter_id
        ) if matter_id else None
        return matter

    def get_queryset(self):
        """ Верните соответствующие экземпляры. """
        qs = super().get_queryset()
        user = self.request.user
        matter = self.get_matter(user) \
            if self.action in ['list', 'retrieve'] else None
        if matter is None:
            referrals = models.Matter.objects.select_related('referral').\
                filter(referral__mediator_id=user.pk)
            ids = list(referrals.values_list('mediator_id', flat=True))
            return qs.filter(mediator_id__in=ids + [user.pk])
        else:
            return qs.filter(mediator_id=matter.mediator_id)


class ChecklistEntryViewSet(BaseMediatorRelatedViewSet):
    """CRUD набор представлений api для модели `ChecklistEntry`
    Для `List", "Retrieve":
        - параметр запроса `matter` не задан - возвращает только экземпляры адвоката
        - установлено значение "дело` - вернуть экземпляры поверенного дела

    Для `Create`, `Update`, `Delete` - возвращать только экземпляры user mediator

    """
    queryset = models.ChecklistEntry.objects.all()
    serializer_class = serializers.ChecklistEntrySerializer
    filterset_class = filters.ChecklistEntryFilter
    search_fields = (
        'description',
    )
    ordering_fields = (
        'id',
        'description',
        'created',
        'modified',
    )


class StageViewSet(BaseMediatorRelatedViewSet):
    """CRUD набор представлений api для модели "Stage"

    Для `List", "Retrieve":
        - параметр запроса `matter` не задан - возвращает только экземпляры адвоката
        - установлено значение "дело` - вернуть экземпляры поверенного дела

    Для `Create`, `Update`, `Delete` - возвращать только экземпляры user mediator
    """
    queryset = models.Stage.objects.all()
    serializer_class = serializers.StageSerializer
    filterset_class = filters.StageFilter
    search_fields = (
        'title',
    )
    ordering_fields = (
        'id',
        'title',
        'created',
        'modified',
    )
    ordering = ('-modified',)
