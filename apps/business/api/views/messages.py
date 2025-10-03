from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ....core.api import views
from ... import models
from .. import filters, serializers
from .core import BusinessViewSetMixin


class MatterPostViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    views.BaseViewSet
):
    """ Набор представлений API для модели `Matter Post`.
    Обеспечьте действия по созданию, извлечению и перечислению.
    """
    queryset = models.MatterPost.objects.all().select_related(
        'last_comment',
        'last_comment__author',
    ).prefetch_related(
        'attachments',
        'participants',
        'last_comment__participants',
        'last_comment__attachments',
        'comments'
    )
    serializer_class = serializers.MatterPostSerializer
    filterset_class = filters.MatterPostFilter
    permissions_map = {
        'default': (IsAuthenticated,),
    }
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
        qs = super().get_queryset().filter(
            participants__in=[self.request.user]
        ).distinct()
        return qs

    @action(methods=['post'], detail=True, url_path='mark_read', )
    def mark_read(self, request, **kwargs):
        """ Отметьте сообщение как прочитанное. """
        post = self.get_object()
        if request.user.is_client:
            models.MatterPost.objects.filter(pk=post.pk).update(
                seen_by_client=True
            )
            post.comments.update(seen_by_client=True)
        elif request.user.is_mediator:
            models.MatterPost.objects.filter(pk=post.pk).update(seen=True)
            post.comments.update(seen=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='mark_unread', )
    def mark_unread(self, request, **kwargs):
        """Mark post as unread"""
        post = self.get_object()
        if request.user.is_client:
            models.MatterPost.objects.filter(pk=post.pk).update(
                seen_by_client=False
            )
            post.comments.update(seen_by_client=False)
        elif request.user.is_mediator:
            models.MatterPost.objects.filter(pk=post.pk).update(seen=False)
            post.comments.update(seen=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        """ Удаляет связанные комментарии перед удалением записи. """
        post = self.get_object()
        participants = post.participants
        participants.remove(request.user)
        size = participants.count()
        if size == 0:
            post.comments.all().delete()
            self.perform_destroy(post)
        else:
            for obj in post.comments.all():
                obj.deleted_participants.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MatterCommentViewSet(
    BusinessViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    views.BaseViewSet
):
    """ Набор представлений API для модели "Комментарий по делу".
    Обеспечьте действия по созданию, извлечению и перечислению.
    """
    queryset = models.MatterComment.objects.select_related(
        'author',
        'post',
    ).prefetch_related(
        'attachments',
        'participants',
        'post__participants',
        'post__matter__mediator__user',
    )
    serializer_class = serializers.MatterCommentSerializer
    permissions_map = {
        'default': (IsAuthenticated,),
    }
    filterset_class = filters.MatterCommentFilter
    ordering_fields = (
        'created',
        'modified',
    )

    def get_queryset(self):
        qs = super().get_queryset().filter(
            participants__in=[self.request.user]
        ).exclude(
            deleted_participants__in=[self.request.user]
        ).distinct()
        return qs

    def list(self, request, *args, **kwargs):
        post_id = request.query_params.get('post')
        if request.user.is_client:
            models.MatterPost.objects.filter(id=post_id).update(
                seen_by_client=True,
            )
        elif request.user.is_mediator:
            models.MatterPost.objects.filter(id=post_id).update(
                seen=True,
            )
        queryset = self.filter_queryset(self.get_queryset())
        # Модуль автоматического изменения статуса закомментирования
        #if request.user.is_client:
        #    queryset.all().update(seen_by_client=True)
        #elif request.user.is_mediator:
        #    queryset.all().update(seen=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='mark_read', )
    def mark_read(self, request, **kwargs):
        """ Отметьте комментарий как прочитанный. """
        try:
            comment = self.get_object()
            if request.user.is_client:
                models.MatterComment.objects.filter(pk=comment.pk).update(
                    seen_by_client=True
                )
            elif request.user.is_mediator:
                models.MatterComment.objects.filter(pk=comment.pk).update(
                    seen=True
                )
        except:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='mark_unread', )
    def mark_unread(self, request, **kwargs):
        """ Отметить комментарий как непрочитанный """
        comment = self.get_object()
        if request.user.is_client:
            models.MatterComment.objects.filter(pk=comment.pk).update(
                seen_by_client=False,
            )
            models.MatterPost.objects.filter(pk=comment.post.pk).update(
                seen_by_client=False,
            )
        elif request.user.is_mediator:
            models.MatterComment.objects.filter(pk=comment.pk).update(
                seen=False
            )
            models.MatterPost.objects.filter(pk=comment.post.pk).update(
                seen=False,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        participants = instance.participants
        participants.remove(request.user)
        size = participants.count()
        if size == 0:
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
