from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, mixins, response, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.business.models.posted_matters import PostedMatter
from ....business.api.serializers.external_overview import (
    ClientOverviewSerializer,
)
from ....business.models import Matter
from ....core.api.views import BaseViewSet, UserAgentLoggingMixin
from ....users import models
from ...api import filters, permissions, serializers
from ..filters import MediatorSearchFilter
from ..serializers.extra import MediatorSearchSerializer
from .utils.verification import complete_signup


class ClientViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    BaseViewSet
):
    """ Конечная точка пользователя приложения для поиска пользователей и регистрации. """
    serializer_class = serializers.ClientSerializer
    queryset = models.Client.objects.select_related(
        'user',
        'country',
        'state',
        'city',
        'city__region',
        'user__timezone',
    ).prefetch_related(
        'user__specialities',
        'user__activities',
        'user__activities__matter',
        'matters__mediator',
        'matters',
    )
    permissions_map = {
        'create': (AllowAny,),
    }
    filterset_class = filters.ClientFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
        'organization_name',
    ]
    ordering_fields = [
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
        'organization_name',
    ]
    # Объяснение:
    # Мы изменили lookup_value_regex, чтобы избежать сворачивания URL-адресов наборов просмотров
    # например, когда у вас установлено представление "пользователи" и "пользователи/адвокат",
    # без этого набор представлений свернется с at `users` таким образом, что
    # набор просмотров пользователей мы используем часть URL-адреса "адвокат" в качестве pk 
    # для поиска в метод извлечения.
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """ Добавьте mediator_id qs, используя параметры запроса """
        qs = super().get_queryset()
        qp = self.request.query_params
        print(qp)
        mediator_id = qp.get('mediator', None)
        search = qp.get('search', None)
        if search or search == '':
            print("search!!")
            return qs.filter(address1="1000")
        if mediator_id:
            return qs.filter(
                Q(matters__mediator_id=mediator_id) |
                Q(matters__shared_with=mediator_id)
            ).distinct()
        return qs

    def create(self, request, *args, **kwargs):
        """Register user and return client profile."""
        serializer = serializers.ClientRegisterSerializer(
            data=request.data,
            context={
                'invite_uuid': self.request.query_params.get(
                    'invite_uuid', None)
            }
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save(self.request)
        headers = self.get_success_headers(serializer.validated_data)
        serializer = serializers.ClientSerializer(
            instance=user.client
        )

        complete_signup(
            self.request._request,
            user,
            settings.ACCOUNT_EMAIL_VERIFICATION,
            None
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(
        detail=True, methods=['GET'],
        url_path='matter_overview/(?P<matter_id>[^/.]+)'
    )
    def matter_overview(self, request, *args, **kwargs):
        """
        Проверяет разрешения клиента и
        возвращает список matter (обзоры)
        """
        client = self.get_object()
        from apps.business.api.serializers.matter import (
            MatterOverviewSerializer,
        )
        try:
            matter = client.matters.get(id=self.kwargs['matter_id'])
            serializer = MatterOverviewSerializer(
                matter,
                context={'request': request},
            )
            return response.Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """
        Проверяет разрешения клиента и
        возвращает сведения об обзоре панели мониторинга
        """
        client = self.get_object()
        serializer = ClientOverviewSerializer(
            client, context={'request': request},
        )
        return response.Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def posted_matters(self, request, *args, **kwargs):
        """
            Проверяет разрешения клиента и
            возвращает материалы, отправленные клиентом
        """
        is_active = request.query_params.get('is_active', '')
        is_hidden_for_client = request.query_params.get('is_hidden_for_client')
        client = self.get_object()
        from apps.business.api.serializers.posted_matters import (
            PostedMatterSerializer,
        )
        posted_matters = client.posted_matters
        if is_active == 'true':
            posted_matters = posted_matters.filter(
                status=PostedMatter.STATUS_ACTIVE
            )
        elif is_active == 'false':
            posted_matters = posted_matters.filter(
                status=PostedMatter.STATUS_INACTIVE
            )
        if is_hidden_for_client == 'true':
            posted_matters = posted_matters.filter(is_hidden_for_client=True)
        elif is_hidden_for_client == 'false':
            posted_matters = posted_matters.filter(is_hidden_for_client=False)

        page = self.paginate_queryset(queryset=posted_matters.all())

        if page is not None:
            serializer = PostedMatterSerializer(posted_matters, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)

        serializer = PostedMatterSerializer(
            posted_matters, many=True
        )
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def search_mediators(self, request, *args, **kwargs):
        """Search Mediator."""
        try:
            filterer = MediatorSearchFilter()
            is_sharable = request.query_params.get('sharable', 'false')
            matter = request.query_params.get('matter', None)
            if is_sharable == 'true':
                if matter:
                    users = models.AppUser.objects.shared_to_matter(
                        Matter.objects.get(pk=matter))
                else:
                    users = models.AppUser.objects.available_for_share()
                mediators = models.Mediator.objects\
                    .filter(user__in=users)\
                    .exclude(user=request.user)
            else:
                mediators = models.Mediator.objects.verified()\
                    .exclude(user=request.user)
            mediators = filterer.filter_queryset(request, mediators, None)

            searched_items = set(mediators)

            page = self.paginate_queryset(queryset=list(searched_items))
            if page is not None:
                serializer = MediatorSearchSerializer(page, many=True)
                return self.paginator.get_paginated_response(
                    data=serializer.data)

            serializer = MediatorSearchSerializer(
                searched_items,
                many=True
            )
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                data={'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def get_contacts(self, request, *args, **kwargs):
        """ возвращает список контактов клиента  """
        client = self.get_object()
        contacts = client.contacts()
        contact_users = get_user_model().objects.filter(id__in=contacts)
        page = self.paginate_queryset(queryset=list(contact_users))
        serializer = serializers.AppUserShortSerializer(
            contact_users, many=True
        )
        if page is not None:
            serializer = serializers.AppUserShortSerializer(page, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)
        return Response(
            status=status.HTTP_200_OK,
            data=serializer.data
        )

    @action(detail=True, methods=['POST'])
    def add_contact(self, request, *args, **kwargs):
        """ Добавить адвоката в качестве контакта  """
        from apps.business.models.matter import Lead

        client = self.get_object()
        mediator_id = request.data.get("client", None)
        try:
            mediator = models.Mediator.objects.get(pk=mediator_id)
            Lead.objects.get_or_create(mediator=mediator, client=client)
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except models.Mediator.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": "Mediator profile does not exist"
                }
            )
        except ValueError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": str(e)
                }
            )


class CurrentClientView(
    UserAgentLoggingMixin,
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView,
):
    """ Извлеките и обновите профиль клиента пользователя.
    Принимает методы GET, PUT и PATCH.
    Поля, доступные только для чтения: user, specialities_data.
    """
    serializer_class = serializers.ClientSerializer 
    permission_classes = IsAuthenticated, permissions.IsClient

    def get_serializer_class(self):
        """ Верните сериализатор для обновления по запросам `PUT` или `PATCH`. """
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateClientSerializer
        return super().get_serializer_class()

    def get_object(self):
        """ Получите профиль клиента пользователя. """
        return self.request.user.client


class CurrentClientFavoriteViewSet(
    mixins.UpdateModelMixin,
    BaseViewSet
):
    """ Найдите любимого адвоката клиента """

    serializer_class = serializers.ClientFavoriteMediatorSerializer
    permission_classes = IsAuthenticated, permissions.IsClient

    def list(self, request, *args, **kwargs):
        client = request.user.client
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(client).data
        )

    def update(self, request, pk=None):
        client = request.user.client
        if models.Mediator.objects.filter(pk=pk).exists():
            client.favorite_mediators.add(pk)
            mediator = models.Mediator.objects.get(pk=pk)
            mediator.followers.add(client.user)
            return Response(
                status=status.HTTP_200_OK,
                data=self.serializer_class(client).data
            )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Mediator does not exist"}
            )

    def destroy(self, request, pk=None):
        client = request.user.client
        if models.Mediator.objects.filter(pk=pk).exists():
            client.favorite_mediators.remove(pk)
            mediator = models.Mediator.objects.get(pk=pk)
            mediator.followers.remove(client.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Mediator does not exist"}
            )
