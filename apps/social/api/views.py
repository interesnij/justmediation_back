from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.business.models import Lead, Matter, Opportunity
from ...core.api.views import BaseViewSet, CRUDViewSet
from ...users.api.permissions import IsMediatorHasActiveSubscription
from .. import models
from . import filters, permissions, serializers
from .serializers import MessageAttachmentSerializer


class ChatViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    BaseViewSet
):
    lookup_value_regex = '[0-9]+'
    queryset = models.Chats.objects.all().prefetch_related(
        'messages',
        'messages__author',
        'messages__attachment',
        'participants',
        'participants__forum_stats',
        'participants__mediator',
        'participants__mediator__firm_locations',
        'participants__mediator__user',
        'participants__client',
        'participants__client__user',
    )
    filterset_class = filters.ChatFilter
    ordering_fields = ('created', 'single_chat_participants__is_favorite', )
    search_fields = ('participants__first_name', 'participants__last_name', )
    base_permissions = (
        IsAuthenticated,
    )
    serializers_map = {
        'default': serializers.ChatSerializer,
        'update': serializers.UpdateChatSerializer,
        'partial_update': serializers.UpdateChatSerializer,
    }
    permission_classes = base_permissions
    participant_permissions = base_permissions + (
        permissions.IsChatParticipant,
    )
    permissions_map = {
        'default': base_permissions,
        'update': participant_permissions,
        'partial_update': participant_permissions,
    }
    serializer_class = serializers.ChatSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serialized_data = self.get_serializer(page, many=True).data
        else:
            serialized_data = self.get_serializer(queryset, many=True).data
        ordering_fields = request.GET.getlist('ordering', [])
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            serialized_data = sorted(
                serialized_data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )
        if page is not None:
            return self.get_paginated_response(serialized_data)
        return Response(serialized_data)

    def get_queryset(self):
        """Limit returned dispatches to current user."""
        qs = super().get_queryset()
        return qs.available_for_user(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_group = data['is_group']
        participants = data['participants']
        client = None
        mediator = None
        if not is_group and request.user.is_mediator \
                and participants[0].is_client:
            client = participants[0].client
            mediator = request.user.mediator
        elif not is_group and request.user.is_client \
                and participants[0].is_mediator:
            mediator = participants[0].mediator
            client = request.user.client
        is_lead = Lead.objects.filter(
            client=client, mediator=mediator
        ).exists()
        is_matter = Matter.objects.filter(
            client=client, mediator=mediator
        ).exists()
        if not is_lead and not is_matter and client and mediator:
            Opportunity.objects.get_or_create(
                mediator=mediator,
                client=client,
                priority=Opportunity.PRIORITY_MEDIUM
            )
        existing_chat = self.queryset.already_existing_chat(
            serializer.validated_data['participants']
        )
        if existing_chat:
            serializer = self.get_serializer(instance=existing_chat)
            response_status = status.HTTP_200_OK
        else:
            self.perform_create(serializer)
            response_status = status.HTTP_201_CREATED
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=response_status, headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        participants = instance.participants
        participants.remove(request.user)
        size = participants.count()
        if size == 1:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif size == 2:
            instance.is_group = False
        elif size > 2:
            instance.is_group = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET', 'POST'], detail=True)
    def messages(self, request, *args, **kwargs):
        """Viewset for chat messages"""
        chat = self.get_object()
        if request.method == 'GET':
            try:
                last_id = int(request.GET.get('last_id', '0'))
            except Exception:
                last_id = 0

            messages = models.Message.objects.select_related('author').\
                filter(pk__gt=last_id, chat_id=chat.pk).prefetch_related(
                    'attachment'
                ).order_by('-created')

            page = self.paginate_queryset(messages)
            if page is not None:
                serializer = serializers.MessageSerializer(
                    page, many=True, context={'request': request}
                )
                return self.get_paginated_response(serializer.data)

            serializer = serializers.MessageSerializer(
                messages, many=True
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        else:
            attrs = request.data
            attrs['author'] = self.request.user.pk
            attrs['chat'] = chat.pk
            files = attrs.get('files', [])
            serializer = serializers.MessageSerializer(
                data=attrs, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            message = serializer.save()

            for file in files:
                file['message'] = message.id
            files_serializer = MessageAttachmentSerializer(
                data=files,
                many=True
            )
            files_serializer.is_valid(raise_exception=True)
            files_serializer.save()

            return Response(
                status=status.HTTP_201_CREATED,
                data=serializers.MessageSerializer(
                    message, context={'request': request}
                ).data
            )


class MediatorPostViewSet(CRUDViewSet):
    """Viewset for `MediatorPost` model."""
    queryset = models.MediatorPost.objects.all().select_related(
        'author',
        'author__user',
    ).prefetch_related(
        'author__user__specialities',
    )
    filterset_class = filters.MediatorPostFilter
    ordering_fields = ('created', 'title')
    search_fields = ('title', 'body_preview')
    permission_classes = (AllowAny, )
    create_permissions = (
        IsAuthenticated,
        IsMediatorHasActiveSubscription,
    )
    author_permissions = create_permissions + (
        permissions.IsMediatorPostAuthor,
    )
    permissions_map = {
        'default': permission_classes,
        'create': create_permissions,
        'update': author_permissions,
        'partial_update': author_permissions,
        'destroy': author_permissions,
    }
    serializer_class = serializers.MediatorPostSerializer
