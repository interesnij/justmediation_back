from collections import OrderedDict
from django.db import transaction
from django.db.utils import IntegrityError
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination
from drf_multiple_model.viewsets import FlatMultipleModelAPIViewSet
from apps.core.api.views import BaseViewSet
from ...documents import models
from . import filters, serializers
from .serializers import DownloadFolderSerializer


class LimitPagination(MultipleModelLimitOffsetPagination):
    default_limit = 5
    page_count = 0

    def paginate_queryset(self, queryset, request, view=None):
        result = super().paginate_queryset(queryset, request, view)
        self.page_count += len(result)
        return result

    def format_response(self, data):
        self.count = self.max_count

        return OrderedDict([
            ('highest_count', self.max_count),
            ('overall_total', self.total),
            ('page_count', self.page_count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])


class ResourcesView(FlatMultipleModelAPIViewSet, BaseViewSet):
    """ Просмотр доступных пользователю ресурсов. """
    pagination_class = LimitPagination
    filterset_class = filters.ResourceFilter
    search_fields = (
        'title',
    )
    ordering_fields = (
        'id',
        'title',
        'created',
        'modified',
        'owner',
        'matter',
    )

    def get_querylist(self):
        """ Настройте набор запросов и класс сериализатора для каждой модели ресурсов. """
        qp = self.request.query_params
        client_id = qp.get('client', None)
        folders = models.Folder.objects.available_for_user(
            self.request.user
        ).select_related(
            'matter',
            'client',
            'owner',
        ).prefetch_related(
            'shared_with',
            'shared_with__mediator',
            'shared_with__client',
        )
        documents = models.Document.objects.available_for_user(
            self.request.user
        ).select_related(
            'matter',
            'client',
            'owner',
            'created_by',
        ).prefetch_related(
            'shared_with',
            'shared_with__mediator',
            'shared_with__client',
        )
        is_parent = qp.get('is_parent', None)
        try:
            if client_id is not None:
                folders = folders.filter(matter__client__pk=client_id)
                documents = documents.filter(matter__client__pk=client_id)
            if is_parent == 'true':
                folders = folders.filter(parent__isnull=True)
                documents = documents.filter(parent__isnull=True)
        except ValueError:
            folders = models.Folder.objects.none()
            documents = models.Document.objects.none()

        querylist = (
            {
                'queryset': folders,
                'serializer_class': serializers.FolderSerializer,
            },
            {
                'queryset': documents,
                'serializer_class': serializers.DocumentSerializer,
            },
        )

        return querylist

    def format_results(self, results, request):
        """
        Подготавливает параметры сортировки и сортирует результаты, 
        если (по мере) необходимости 
        """
        self.prepare_sorting_fields()
        if self._sorting_fields:
            results = self.sort_results(results)

        if request.accepted_renderer.format == 'html':
            results = {'data': results}

        fields = request.query_params.getlist('ordering', [])
        for field in fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            results = sorted(
                results,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )
        return results


class BaseResourceViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """ Базовое представление для моделей ресурсов (документы и папки).
    Используется для объединения логики crud api для моделей "Документ" и "Папка".
    """
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """Return only user's resources."""
        qp = self.request.query_params
        is_parent = qp.get('is_parent', None)
        client_id = qp.get('client', None)
        qs = super().get_queryset().available_for_user(self.request.user)
        if is_parent == 'true':
            qs = qs.filter(parent__isnull=True)
        if client_id is not None:
            qs = qs.filter(matter__client__pk=client_id)
        return qs

    @action(methods=['post'], detail=True, url_path='duplicate')
    def duplicate(self, request, *args, **kwargs):
        """Duplicate resource."""
        serializer = self.get_serializer(
            instance=self.get_object(),
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer = self.serializer_class(
            context=self.get_serializer_context(),
            instance=serializer.instance
        )

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=['post'], detail=True)
    def add_shared_with(self, request, *args, **kwargs):
        shared_with = request.data.get('shared_with')
        resource = self.get_object()
        for user in shared_with:
            resource.shared_with.add(user)
        resource.save()
        if isinstance(resource, models.Folder):
            data = serializers.FolderSerializer(instance=resource).data
        else:
            data = serializers.DocumentSerializer(instance=resource).data
        try:
            return Response(
                status=status.HTTP_200_OK,
                data=data
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['post'], detail=True)
    def remove_shared_with(self, request, *args, **kwargs):
        shared_with = request.data.get('shared_with')
        resource = self.get_object()
        for user in shared_with:
            resource.shared_with.remove(user)
        resource.save()
        if isinstance(resource, models.Folder):
            data = serializers.FolderSerializer(instance=resource).data
        else:
            data = serializers.DocumentSerializer(instance=resource).data
        try:
            return Response(
                status=status.HTTP_200_OK,
                data=data
            )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )


class FolderViewSet(BaseResourceViewSet):
    """Viewset for `Folder` model."""
    queryset = models.Folder.objects.all().select_related(
        'parent',
        'owner',
        'matter',
        'client',
    ).prefetch_related(
        'shared_with',
        'shared_with__mediator',
        'shared_with__client',
    )
    serializer_class = serializers.FolderSerializer
    update_serializer_class = serializers.UpdateFolderSerializer
    duplicate_resource_serializer = serializers.DuplicateFolderSerializer
    serializers_map = {
        'update': update_serializer_class,
        'partial_update': update_serializer_class,
        'duplicate': duplicate_resource_serializer,
    }
    filterset_class = filters.ResourceFilter
    folder_permissions = (
        IsAuthenticated,
    )
    permissions_map = {
        'update': folder_permissions,
        'partial_update': folder_permissions,
        'duplicate': folder_permissions,
        'destroy': folder_permissions,
    }

    @action(methods=['get'], detail=True)
    def download(self, request, *args, **kwargs):
        """Returns list of documents in the folder."""
        folder = self.get_object()
        documents = folder.documents.all()

        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = DownloadFolderSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DownloadFolderSerializer(documents, many=True)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        if hasattr(document.matter, 'client') and \
                document.matter.client == request.user:
            document.seen = True
            document.save()
        response = super().retrieve(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        """Create folder with handling exception"""
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                data={
                    'detail': 'Same folder with title and matter is existed'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class DocumentViewSet(BaseResourceViewSet):
    """Viewset for `Document` model."""
    queryset = models.Document.objects.all().select_related(
        'created_by',
        'parent',
        'owner',
        'client',
        'matter',
    ).prefetch_related(
        'shared_with',
        'shared_with__mediator',
        'shared_with__client',
    )
    serializer_class = serializers.DocumentSerializer
    update_serializer_class = serializers.UpdateDocumentSerializer
    duplicate_resource_serializer = serializers.DuplicateDocumentSerializer
    serializers_map = {
        'update': update_serializer_class,
        'partial_update': update_serializer_class,
        'duplicate': duplicate_resource_serializer,
    }
    documents_permissions = (
        IsAuthenticated,
    )
    filterset_class = filters.ResourceFilter
    permissions_map = {
        'update': documents_permissions,
        'partial_update': documents_permissions,
        'duplicate': documents_permissions,
        'destroy': documents_permissions,
    }
    search_fields = (
        'title',
    )

    def get_queryset(self):
        """ Возвращаемые документы по типу """
        qp = self.request.query_params
        type = qp.get('type', None)
        qs = super().get_queryset()
        if type is not None:
            return qs.filter(mime_type__startswith=type)
        return qs

    def create(self, request, *args, **kwargs):
        """ Создать документ с обработкой исключения """
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                data={
                    'detail': 'Same document with title and matter is existed'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
