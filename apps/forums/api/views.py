from django.db.models import Count
from django.db.models.query import Prefetch

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.business.models import PostedMatter

from ...core.api.views import BaseViewSet
from ...users.api.permissions import IsMediatorHasActiveSubscription
from .. import models
from ..api import filters, permissions, serializers


class TopicViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   BaseViewSet):
    """Viewset for `topic` model.

    Provide list and retrieve API methods.

    """
    queryset = models.Topic.objects.all().select_related(
        'practice_area',
        'last_comment__author',
        'last_comment__author__mediator',
        'last_comment__author__support',
        'last_comment__author__client',
        'last_comment__author__forum_stats',
        'last_comment__post',
    ).prefetch_related(
        'posts',
        'followers',
        'last_comment__author__specialities',
    )
    serializer_class = serializers.TopicSerializer
    filterset_class = filters.TopicFilter
    ordering_fields = ('created', 'post_count', 'title', 'modified')
    ordering = 'title'
    search_fields = ('title',)
    permission_classes = (AllowAny,)
    permissions_map = {
        'default': (AllowAny,),
        'follow': (IsAuthenticated,),
        'unfollow': (IsAuthenticated,),
    }

    @action(methods=['post'], detail=True, url_path='follow', )
    def follow(self, request, **kwargs):
        """Follow topic."""
        topic = self.get_object()
        topic.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """Unfollow topic."""
        topic = self.get_object()
        topic.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.CreateModelMixin,
                  mixins.DestroyModelMixin,
                  BaseViewSet):
    """Viewset for `post` model.

    Provide list, retrieve and create API methods. Create method only
    available for authenticated users. Update and destroy only available for
    author of the topic.

    """
    queryset = models.Post.objects.annotate(
        Count('followers')
    ).all().select_related(
        'author',
        'author__mediator',
        'author__client',
        'author__owned_enterprise',
        'last_comment',
        'first_comment',
        'last_comment__author',
        'last_comment__author__mediator',
        'last_comment__author__client',
        'last_comment__author__owned_enterprise',
        'last_comment__author__forum_stats',
        'first_comment__author',
        'first_comment__author__mediator',
        'first_comment__author__client',
        'first_comment__author__owned_enterprise',
        'first_comment__author__forum_stats',
    ).prefetch_related(
        'followers',
        'topic__practice_area',
        'topic__followers',
        'topic__posts',
    )
    serializer_class = serializers.PostSerializer
    filterset_class = filters.PostFilter
    ordering_fields = (
        'title',
        'created',
        'modified',
        'comment_count',
        'followers__count',
        'last_comment__created',
    )
    search_fields = (
        'title',
        'first_comment__text',
    )
    permission_classes = (AllowAny,)
    permissions_map = {
        'default': (AllowAny,),
        'create': (IsAuthenticated, ),
        'update': (IsAuthenticated, permissions.IsPostAuthor,),
        'partial_update': (IsAuthenticated, permissions.IsPostAuthor,),
        'opportunities': (
            IsAuthenticated,
            IsMediatorHasActiveSubscription,
        ),
        'follow': (IsAuthenticated,),
        'unfollow': (IsAuthenticated,),
    }
    serializers_map = {
        'create': serializers.PostCreateUpdateSerializer,
        'update': serializers.PostCreateUpdateSerializer,
        'partial_update': serializers.PostCreateUpdateSerializer,
    }

    @action(methods=['GET'], detail=False)
    def opportunities(self, request, *args, **kwargs):
        """Get mediator's opportunities."""
        queryset = self.filter_queryset(
            self.get_queryset().opportunities(request.user)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='follow', )
    def follow(self, request, **kwargs):
        """Follow post."""
        post = self.get_object()
        post.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """Unfollow post."""
        post = self.get_object()
        post.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     BaseViewSet):
    """Viewset for `Comment` model.

    Provide list, retrieve and create API methods. Create method only
    available for authenticated users. Update and destroy only available for
    author of the post.

    """
    queryset = models.Comment.objects.all().with_position().select_related(
        'author',
        'author__forum_stats',
        'author__mediator',
        'author__client',
    ).prefetch_related(
        'author__specialities',
    )
    serializer_class = serializers.CommentSerializer
    filterset_fields = ('post', 'author',)
    ordering_fields = ('title', 'created',)
    search_fields = ('title',)
    permission_classes = (AllowAny,)
    permissions_map = {
        'default': (AllowAny,),
        'create': (IsAuthenticated,),
        'update': (IsAuthenticated, permissions.IsPostAuthor,),
        'partial_update': (IsAuthenticated, permissions.IsPostAuthor,),
        'destroy': (
            IsAuthenticated,
            permissions.IsNotFirstComment,
            permissions.IsPostAuthor
        )
    }


class FollowedPostViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          BaseViewSet):
    """View set for `FollowedPost`model.

     Allow user to follow|unfollow specified post.

     """
    permission_classes = (IsAuthenticated,)
    queryset = models.FollowedPost.objects.select_related(
        'post',
        'post__last_comment',
        'post__last_comment__author',
        'post__last_comment__author__forum_stats',
        'post__first_comment',
        'post__first_comment__author',
        'post__first_comment__author__forum_stats',
    ).prefetch_related(
        'post__last_comment__author__specialities',
        'post__first_comment__author__specialities',
    ).all()
    filterset_class = filters.FollowedPostFilter
    serializer_class = serializers.FollowedPostSerializer
    permissions_map = {
        'default': (IsAuthenticated,)
    }

    def get_queryset(self):
        """Return only user followings."""
        return self.queryset.filter(follower=self.request.user)


class FollowedTopicViewSet(mixins.ListModelMixin, BaseViewSet):
    """
     Allow user to get followed topics.
     """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TopicShortSerializer
    search_fields = (
        'title',
    )
    permissions_map = {
        'default': (IsAuthenticated,)
    }

    def get_queryset(self):
        """Return only user followings."""
        return self.request.user.topics.all()


class PracticeAreaViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """Api view to list all specialities."""
    serializer_class = serializers.PracticeAreaSerializer
    permission_classes = (IsAuthenticated,)
    permissions_map = {
        'default': (IsAuthenticated,),
        'list': (AllowAny,),
        'retrieve': (AllowAny,),
    }
    queryset = models.ForumPracticeAreas.objects.prefetch_related(
        Prefetch(
            'posted_matter',
            queryset=PostedMatter.objects.filter(
                status=PostedMatter.STATUS_ACTIVE
            ).order_by('-created')
        ),
        'posted_matter__currency',
        'posted_matter__proposals',
        'posted_matter__proposals__mediator',
        'posted_matter__proposals__currency',
        'posted_matter__client',
        'posted_matter__client__user',
    )
    search_fields = [
        'title',
    ]
    ordering = 'title'

    @action(methods=['get'], detail=True)
    def posted_matters(self, request, *args, **kwargs):
        practice_area = self.get_object()

        posted_matters = practice_area.posted_matter.all()
        from apps.business.api.serializers.posted_matters import (
            PostedMatterSerializer,
        )
        ordering_fields = request.GET.getlist('ordering', [])
        page = self.paginate_queryset(posted_matters)

        serializer = PostedMatterSerializer(
            posted_matters,
            many=True,
            context={'request': request}
        )

        data = serializer.data
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            data = sorted(
                serializer.data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )

        if page is not None:
            return self.paginator.get_paginated_response(data)

        return Response(
            data=data,
            status=status.HTTP_200_OK
        )
