import logging
from django.db.models.query import Prefetch
from rest_framework import response, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from django_fsm import TransitionNotAllowed
from libs.django_fcm.api.utils import transition_method
from ....core.api import views
from ....users.api.serializers import ParticipantsSerializer
from ....users.models import AppUser
from ... import models, services
from ...signals import new_matter_referred
from ...signals.extra import (
    matter_referral_revoked,
    new_referral_accepted,
    new_referral_declined,
)
from .. import filters, serializers
from ..serializers.matter import MatterDocumentSerializer
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class LeadViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD набор представлений api для Lead модели
    """
    permissions_map = {
        'update': BusinessViewSetMixin.mediator_permissions,
        'partial_update': BusinessViewSetMixin.mediator_permissions,
        'destroy': BusinessViewSetMixin.mediator_permissions,
    }
    queryset = models.Lead.objects.all().select_related(
        'client',
        'client__user',
        'client__state',
        'mediator',
        'mediator__user'
    ).prefetch_related(
        'mediator__user__specialities'
    )
    serializer_class = serializers.LeadSerializer
    serializers_map = {
        'update': serializers.UpdateLeadSerializer,
        'partial_update': serializers.UpdateLeadSerializer,
    }
    filterset_class = filters.LeadFilter
    search_fields = (
        'topic__title',
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@mediator__user__first_name',
        '@mediator__user__last_name',
        'mediator__user__email',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'topic__title',
        ('client__first_name', 'client__user__first_name'),
        ('client__last_name', 'client__user__last_name'),
        ('client__email', 'client__user__email'),
        'client__organization_name',
        'mediator__user__first_name',
        'mediator__user__last_name',
        'mediator__user__email',
    )


class MatterViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD набор представлений api для Matter модели

    Поля, доступные "только для чтения", когда вопрос не находится "на рассмотрении":
        * `city`
        * `state`
        * `country`
        * `rate`
        * `rate_type`
        * `title`
        * `description`
        * `code`

    """
    # removed with_totals()
    queryset = models.Matter.objects.all().select_related(
        'client',
        'client__user',
        'client__country',
        'client__state',
        'client__city',
        'mediator',
        'mediator__user',
        'speciality',
        'currency',
        'country',
        'state',
        'city',
        'stage',
        'fee_type',
    ).prefetch_related(
        # пользовательская предварительная выборка для `начальных` конвертов только по соображениям 
        # производительности последние конверты должны быть отправлены первыми
        # Prefetch(
        #     'envelopes',
        #     queryset=Envelope.objects.filter(type=Envelope.TYPE_INITIAL)
        #     .order_by('-id')
        #     .prefetch_related('documents')
        # ),
        Prefetch(
            'activities',
            queryset=models.Activity.objects.order_by('-created')
        ),
        'shared_with',
        # добавьте эту предварительную выборку из-за поля `user_type`
        'shared_with__mediator',
        'shared_with__support',
        'shared_with__client',
        'billing_item',
        'billing_item__billing_items_invoices',
        'documents',
        'folders',
        'posts',
        'posts__participants',
        'invoices',
        'invoices__billing_items',
    )
    serializer_class = serializers.MatterSerializer
    transition_result_serializer_class = serializers.MatterSerializer
    serializers_map = {
        'retrieve': serializers.MatterDetailSerializer,
        'update': serializers.UpdateMatterSerializer,
        'partial_update': serializers.UpdateMatterSerializer,
        'share_with': serializers.ShareMatterSerializer,
        # Если для перехода требуются данные, установите для них соответствующий сериализатор.
        'send_referral': serializers.ReferralSerializer,
        'resend_referral': serializers.ReferralSerializer,
        'accept_referral': None,
        'close': None,
        'open': None
    }
    permissions_map = {
        # только адвокаты могут создавать новые дела
        'create': BusinessViewSetMixin.mediator_permissions,
        'update': (BusinessViewSetMixin.mediator_support_permissions,),
        'share_with': (BusinessViewSetMixin.mediator_support_permissions,),
        # адвокат и помощник юриста могут вносить изменения в дела
        'partial_update': (BusinessViewSetMixin.support_permissions,),
        'close': (BusinessViewSetMixin.support_permissions,),
        'open': (BusinessViewSetMixin.support_permissions,),
        # статусы разрешения
        'send_referral': (BusinessViewSetMixin.mediator_support_permissions,),
        'resend_referral': (
            BusinessViewSetMixin.mediator_support_permissions,),
        'accept_referral': (BusinessViewSetMixin.mediator_support_permissions,)
    }
    filterset_class = filters.MatterFilter
    search_fields = (
        'code',
        'title',
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@mediator__user__first_name',
        '@mediator__user__last_name',
        'mediator__user__email',
    )
    ordering_fields = (
        'id',
        'title',
        'created',
        'modified',
        'client__user__first_name',
        'mediator__user__first_name',
        'start_date',
    )

    def get_queryset(self):
        """ По соображениям производительности помечайте qs флагом `_is_shared`. """
        qs = super().get_queryset().with_is_shared_for_user(self.request.user)
        return qs

    def get_object(self):
        matter = models.Matter.objects.get(pk=self.kwargs['pk'])
        matter_ids = self.get_queryset().values_list('pk', flat=True)
        if matter and matter.pk not in matter_ids:
            raise NotFound(
                detail='You have no access permission to that matter')

        return super().get_object()

    def create(self, request, *args, **kwargs):
        request_data = request.data
        """ Дескриптор в случае, если клиент является invite uuid, замените ключ `client`
        с помощью `invite`, если значение для ключа `client` равно invite uuid """
        try:
            if request_data.get('invite'):
                if 'client' in request_data.keys():
                    del request_data['client']
            else:
                if request_data.get('client') and \
                        not str(request_data['client']).isdigit():
                    request_data['invite'] = request_data['client']
                    del request_data['client']

            serializer = serializers.MatterSerializer(
                data=request_data, context=super().get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            headers = self.get_success_headers(data)
            matter = serializer.save()
            attachments = request.data.get('attachment', [])
            for attachment in attachments:
                attachment_serializer = MatterDocumentSerializer(
                    data={
                        'file': attachment,
                        'owner': request.user.id,
                        'created_by': request.user.id,
                        'matter': matter.id
                    }
                )
                attachment_serializer.is_valid(raise_exception=True)
                attachment_serializer.save()
            matter.save()
            serializer = serializers.MatterSerializer(
                instance=matter
            )

            return response.Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            return response.Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })

    # сигнатура методов не имеет значения, потому что они переопределены
    # в декораторах

    @action(detail=True, methods=['POST'])
    @transition_method('open')
    def open(self, *args, **kwargs):
        """Update matter status to `Open`."""

    @action(detail=True, methods=['POST'])
    @transition_method('close')
    def close(self, *args, **kwargs):
        """Update matter status to `Close`."""

    @action(detail=True, methods=['POST'], url_path='share')
    def share_with(self, request, *args, **kwargs):
        """ Поделитесь (`сослаться`) вопросом с другими пользователями приложения.
        Этот метод позволяет поделиться материалом с другими пользователями приложения, 
        чтобы они могли помочь original matter mediator управлять им.
        """
        matter = get_object_or_404(self.get_queryset(), **kwargs)

        if (matter.status in [models.Matter.STATUS_CLOSE]):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "It's not allowed to share matters "
                                "in `pending` or `draft` statuses"}
            )
        serializer = self.get_serializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # этот метод может добавлять новых пользователей и удалять существующих, если они были
        # не передается в зависимости от `user_type`
        services.share_matter(
            request.user, matter, **serializer.validated_data
        )
        matter.refresh_from_db()
        return response.Response(
            data=serializers.MatterSerializer(matter).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'], url_path='send_referral')
    def send_referral(self, request, *args, **kwargs):
        # Отправьте запрос о направлении другому адвокату

        matter = get_object_or_404(self.get_queryset(), **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            if matter.mediator.user != request.user:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "You are not principle of the matter"}
                )
            data = serializer.validated_data
            referral = models.Referral.objects.create(**data)
            matter.referral = referral
            matter.send_referral()
            matter.save()
            new_matter_referred.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            return response.Response(
                data=serializers.MatterSerializer(
                    matter, context={'request': request}
                ).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed as e:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(detail=True, methods=['POST'], url_path='resend_referral')
    def resend_referral(self, request, *args, **kwargs):
        # Повторно отправьте запрос о направлении адвокату

        matter = get_object_or_404(self.get_queryset(), **kwargs)
        try:
            if matter.mediator.user != request.user:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "You are not principle of the matter"}
                )
            if matter.status != models.Matter.STATUS_REFERRAL \
                    or not matter.referral:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "The matter is not referred"}
                )
            new_matter_referred.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            return response.Response(
                data=serializers.MatterSerializer(
                    matter, context={'request': request}
                ).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed as e:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(detail=True, methods=['POST'], url_path='recall_referral')
    def recall_referral(self, request, *args, **kwargs):
        # Отозвать запрос на направление

        matter = get_object_or_404(self.get_queryset(), **kwargs)
        try:
            if matter.mediator.user != request.user:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": "You are not principle of the matter"}
                )
            matter.revoke_referral()
            matter.save()
            matter_referral_revoked.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            return response.Response(
                data=serializers.MatterSerializer(
                    matter, context={'request': request}
                ).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed as e:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(detail=True, methods=['POST'], url_path='accept_referral')
    def accept_referral(self, request, *args, **kwargs):
        # Принять запрос о направлении от другого адвоката

        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            new_referral_accepted.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
            matter.delete_referral()
            matter.accept_referral()
            matter.referral_ignore_mediator = None
            matter.save()
            return response.Response(
                data=serializers.MatterSerializer(matter).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'], url_path='ignore_referral')
    def ignore_referral(self, request, *args, **kwargs):
        # Игнорировать запрос о направлении от другого адвоката

        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            if not matter.referral:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={'detail': 'The matter is not referred'}
                )
            if matter.referral.mediator.user != request.user:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={'detail': 'You are not referred mediator'}
                )
            new_referral_declined.send(
                sender=models.Matter,
                instance=matter,
                notification_sender=self.request.user,
                user=self.request.user
            )
           # нвдо сделать так, чтобы объект ссылки был удален, перейдите к модели matter
            matter.ignore_referral(request.user)
            matter.save()
            return response.Response(
                data=serializers.MatterSerializer(matter).data,
                status=status.HTTP_200_OK
            )
        except TransitionNotAllowed:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def participants(self, request, *args, **kwargs):
        """ Вернуть доступных участников """
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            shared_with = matter.shared_with.all()
            if request.user.is_client:
                principal = AppUser.objects.filter(
                    pk=matter.mediator.user.pk
                )
                participants = shared_with | principal
            else:
                client = AppUser.objects.filter(
                    pk=matter.client.user.pk
                )
                participants = shared_with | client
            participants = participants.distinct()
            page = self.paginate_queryset(participants)
            if page is not None:
                serializer = ParticipantsSerializer(
                    page, context={"request": request}, many=True
                )
                return self.get_paginated_response(serializer.data)
            serializer = ParticipantsSerializer(
                participants, context={"request": request}, many=True
            )
            return response.Response(
                status=status.HTTP_200_OK,
                data=serializer.data
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['PUT'])
    def leave_matter(self, request, *args, **kwargs):
        """ Оставьте материал, которым делятся с """
        try:
            matter = get_object_or_404(self.get_queryset(), **kwargs)
            matter.shared_with.remove(request.user.pk)
            return response.Response(
                status=status.HTTP_200_OK,
                data={'success': True}
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'success': False}
            )


class OpportunityViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """ Просмотр, установленный для модели возможностей. """
    permissions_map = {
        'update': BusinessViewSetMixin.mediator_permissions,
        'partial_update': BusinessViewSetMixin.mediator_permissions,
        'destroy': BusinessViewSetMixin.mediator_permissions,
    }
    queryset = models.Opportunity.objects.all().select_related(
        'client',
        'client__user',
        'client__state',
        'mediator',
        'mediator__user',
    ).prefetch_related(
        'mediator__user__specialities',
    )
    serializer_class = serializers.OpportunitySerializer
    filterset_class = filters.OpportunityFilter
    search_fields = (
        '@client__user__first_name',
        '@client__user__last_name',
        'client__user__email',
        'client__organization_name',
        '@mediator__user__first_name',
        '@mediator__user__last_name',
        'mediator__user__email',
    )
    ordering_fields = (
        'id',
        'created',
        'modified',
        'client__user__first_name',
        'client__user__last_name',
        'client__user__email',
        'client__organization_name',
        'mediator__user__first_name',
        'mediator__user__last_name',
        'mediator__user__email',
    )
