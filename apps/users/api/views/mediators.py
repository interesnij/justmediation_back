from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.db.models.query import Prefetch
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from apps.business.api.serializers.external_overview import (
    MediatorDetailedOverviewSerializer,
    LeadAndClientSerializer,
)
from apps.business.api.serializers.posted_matters import (
    MediatorProposalSerializer,
)
from apps.business.models import PostedMatter, Proposal
from apps.business.models.matter import Lead, Matter
from apps.core.api.views import BaseViewSet, UserAgentLoggingMixin
from apps.finance.services import stripe_subscriptions_service
from apps.social.models import Chats
from apps.users import services
from .. import permissions, serializers
from ...models import Mediator, Client, Enterprise, EnterpriseMembers, Invite
from ..filters import (
    MediatorFilter,
    IndustryContactsSearchFilter,
    IndustryContactsTypeFilter,
    LeadClientFilter,
    LeadClientSearchFilter,
)
from ..serializers.industry_contacts import (
    IndustryContactMediatorDetails,
    IndustryContactDetails,
    IndustryContactSerializer,
)
from .utils.verification import complete_signup


class MediatorViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    BaseViewSet
):
    """ Представление для регистрации и поиска адвокатов.
    Конечная точка для регистрации, извлечения и поиска профилей адвокатов пользователей

    Чтобы получить информацию, на которую подписываются пользователи, вы должны сделать запрос 
    следующим образом: `users/mediators/?followed=true`.

    Это представление доступно только для чтения (за исключением регистрации), поскольку 
    пользователь может только редактировать свой собственный профиль адвоката.
    Примечание: пользователь может создать профиль адвоката только один раз
    Функциональность редактирования представлена в режиме текущего просмотра
    """
    permissions_map = {
        'default': (IsAuthenticated,),
        'create': (AllowAny,),
        'follow': (permissions.CanFollow,),
        'unfollow': (permissions.CanFollow,),
        'overview': (IsAuthenticated, permissions.IsMediatorFreeAccess,),
        'update_contact': (IsAuthenticated, permissions.IsMediatorFreeAccess,
                           permissions.IsOwner,),
    }
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.MediatorSerializer
    serializers_map = {
        'create': serializers.MediatorRegisterSerializer,
        'retrieve': serializers.MediatorDetailSerializer,
        'validate_registration': serializers.MediatorRegisterSerializer,
        'leads_and_clients': LeadAndClientSerializer,
    }
    queryset = Mediator.objects.real_users().select_related(
        'user',
        'user__client',
        'user__owned_enterprise',
        'fee_currency',
    ).prefetch_related(
        Prefetch(
            'matters', queryset=Matter.objects.order_by('-modified')
        ),
        Prefetch(
            'user__chats', queryset=Chats.objects.annotate(
                msg_count=Count('messages')
            ).filter(msg_count__gt=0).prefetch_related(
                'messages', 'participants'
            ).order_by('-modified')
        ),
        'matters__client',
        'matters__mediator',
        'matters__speciality',
        'matters__fee_type',
        'followers',
        'education',
        'education__university',
        'user__specialities',
        'firm_locations',
        'firm_locations__country',
        'firm_locations__state',
        'firm_locations__city',
        'firm_locations__city__region',
        'practice_jurisdictions',
        'practice_jurisdictions__country',
        'practice_jurisdictions__state',
        'fee_types',
        'appointment_type',
        'payment_type',
        'spoken_language',
        'registration_attachments',
        'user__billing_item__billing_items_invoices',
    )
    filterset_class = MediatorFilter
    search_fields = [
        '@user__first_name',
        '@user__last_name',
        'user__email',
    ]
    ordering_fields = [
        'featured',
        'distance',
        'modified',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    # Объяснение:
    # Мы изменили lookup_value_regex, чтобы избежать сворачивания URL-адресов наборов просмотров
    # например, когда у вас установлено представление "пользователи" и "пользователи/адвокат"
    # без этого набор представлений свернется с at `users` таким образом, что
    # набор просмотров пользователей мы используем часть URL-адреса "адвокат" в качестве pk 
    # для поиска в метод извлечения
    lookup_value_regex = '[0-9]+'

    def get_queryset(self):
        """ Добавьте расстояние к qs, используя данные из query_params. """
        qs = super().get_queryset()
        qp = self.request.query_params
        if qp.get('is_verified') == "true":
            return qs.verified()
        return qs.with_distance(
            longitude=qp.get('longitude'),
            latitude=qp.get('latitude')
        )

    def create(self, request, *args, **kwargs):
        """ Зарегистрируйте пользователя и верните профиль адвоката.
        Существует следующий рабочий процесс:
        1. Создайте нового пользователя
        2. Создайте адвоката и связанные с ним объекты
        3. Создайте нового клиента с настроенным способом оплаты (на основе соответствующего
            Намерение настройки).
        """
        serializer = serializers.MediatorRegisterSerializer(
            data=request.data,
            context={
                'invite_uuid': self.request.query_params.get(
                    'invite_uuid', None)
            }
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Если представление выдает исключение, откатывает транзакцию
        # пользователя и поверенного для создания.
        headers = self.get_success_headers(data)
        payment_method = data.get('payment_method', None)
        with transaction.atomic():
            user = serializer.save(self.request)
            if payment_method is not None:
                stripe_subscriptions_service.\
                    create_customer_with_attached_card(
                        user=user,
                        payment_method=payment_method
                    )
        serializer = serializers.MediatorSerializer(
            instance=user.mediator
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

    @action(methods=['post'], detail=True, url_path='onboarding', )
    def onboarding(self, request, **kwargs):
        """ Вступающий в должность адвокат """
        mediator_id = self.kwargs['pk']
        serializer = serializers.MediatorOnboardingSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mediator = serializer.update(mediator_id, data)
        serializer = serializers.MediatorSerializer(
            instance=mediator
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True, url_path='follow', )
    def follow(self, request, **kwargs):
        """ Следуйте за адвокатом. """
        mediator = self.get_object()
        mediator.followers.add(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True, url_path='unfollow', )
    def unfollow(self, request, **kwargs):
        """ Отписаться от адвоката. """
        mediator = self.get_object()
        mediator.followers.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=False, url_path='validate-registration')
    def validate_registration(self, request, **kwargs):
        """ Подтвердите шаги по регистрации адвоката.
        Приложение имеет многоступенчатый процесс регистрации на 3 страницах, который не является
        удобно проверять с помощью одного запроса. Чтобы сделать его более простым в 
        использовании, добавлены отдельные конечные точки API для проверки каждой регистрации
        страница отдельно. Это позволяет предотвратить перенаправление пользователя на следующий
        этап регистрации, если текущий этап недействителен во внешнем интерфейсе.

        Текущая проверка регистрации позволяет проверять только шаги:
            - 1-й - `email`, `password1`, `password2`
            - 2d - все оставленные поля для регистрации адвоката, кроме `Stripe`
                информация об оплате.
        """
        stage_serializer = serializers.MediatorRegisterValidateSerializer(
            data=request.query_params
        )
        stage_serializer.is_valid(raise_exception=True)
        stage = stage_serializer.validated_data['stage']
        reg_stage_serializer_map = {
            'first': serializers.MediatorRegisterValidateFirstStepSerializer,
            'second': serializers.MediatorRegisterValidateSecondStepSerializer
        }
        serializer = reg_stage_serializer_map[stage](data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def overview(self, request, *args, **kwargs):
        """ Возвращает обзорные сведения для панели управления адвокатом. """
        mediator = get_object_or_404(self.queryset, **kwargs)
        serializer = MediatorDetailedOverviewSerializer(mediator, context={
            'request': request
        })
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['PUT'])
    def share_contact(self, request, *args, **kwargs):
        """ Делится контактами с другими адвокатами """
        # Проверка разрешений адвоката.
        self.get_object()

        object_map = {
            True: Invite,
            False: Client
        }
        from apps.social.api.serializers import ContactShareSerializer
        serializer = ContactShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_pending = serializer.validated_data['is_pending']

        try:
            contact = object_map[is_pending].objects.get(
                pk=request.data.get('contact_id')
            )
        except Exception:
            raise Http404('No %s matches the given query.' %
                          object_map[is_pending]._meta.object_name)

        contact.shared_with.add(*serializer.validated_data['shared_with'])

        return Response(
            data={},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def leads_and_clients(self, request, *args, **kwargs):
        """ Возвращает лиды адвоката и клиентов. """
        mediator = get_object_or_404(self.queryset, **kwargs)
        try:
            search_filter = LeadClientSearchFilter()
            type_filter = LeadClientFilter()

            leads_clients = Client.mediator_clients_and_leads(mediator).\
                select_related(
                    'user',
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    Prefetch(
                        'matters',
                        queryset=Matter.objects.filter(mediator=mediator)
                    ),
                    Prefetch(
                        'leads',
                        queryset=Lead.objects.filter(
                            status=Lead.STATUS_CONVERTED, mediator=mediator
                        )
                    ),
                ).distinct()
            leads_clients = search_filter.search_lead_client(
                request, leads_clients
            )
            leads_clients = type_filter.filter_type(request, leads_clients)

            invites = Invite.get_pending_mediator_invites(mediator).\
                select_related(
                    'country',
                    'state',
                    'city',
                    'city__region',
                ).prefetch_related(
                    'matters'
                )
            invites = search_filter.search_lead_client(request, invites)
            invites = type_filter.filter_type(request, invites)

            leads_and_clients = set(leads_clients) | set(invites)

            page = self.paginate_queryset(queryset=list(leads_and_clients))
            ordering_fields = request.GET.getlist('ordering', [])
            if page is not None:
                serializer = LeadAndClientSerializer(
                    page,
                    many=True,
                    context={'request': request}
                )
            else:
                serializer = LeadAndClientSerializer(
                    leads_and_clients,
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
                    data,
                    key=lambda k: (k[field] is not None, k[field]),
                    reverse=reverse
                )
            if page is not None:
                return self.get_paginated_response(data)
            else:
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
        except Exception:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['DELETE'])
    def remove_leads_and_clients(self, request, *args, **kwargs):
        """ Удаление потенциальных клиентов из списка контактов """
        mediator = self.get_object()
        try:
            user_id = request.data.get('user_id', None)
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                Invite.objects.filter(uuid=user_id).delete()
            else:
                Lead.objects.filter(
                    mediator=mediator, client=user_id
                ).delete()
                Matter.objects.filter(
                    mediator=mediator, client=user_id
                ).delete()
            return Response(
                data={"success": True},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['POST'])
    def change_user_type(self, request, *args, **kwargs):
        """ Адвокат позволяет изменять типы пользователей (lead, client) """
        mediator = self.get_object()
        user_id = request.data.get('user_id')
        type = request.data.get('type', 'client')
        print("type", type)
        try:
            is_invite = False
            try:
                is_invite = not isinstance(int(user_id), int)
            except ValueError:
                is_invite = True
            if is_invite:
                print("is_invite", is_invite)
                Invite.objects.filter(uuid=user_id).update(client_type=type)
            else:
                lead = mediator.leads.get(client=user_id)
                print("lead", lead.id)
                if type == 'client':
                    lead.status = Lead.STATUS_CONVERTED
                elif type == 'lead' and \
                        Matter.objects.filter(
                            client=lead.client, mediator=mediator
                        ).count() == 0:
                    lead.status = Lead.STATUS_ACTIVE
                else:
                    return Response(
                        data={
                            "success": False,
                            "detail": "Client who has matters can not changed"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                lead.save()
        except Lead.DoesNotExist:
            return Response(
                data={"success": False},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={"success": True},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'])
    def industry_contacts(self, request, *args, **kwargs):
        """ Возвращает контакты юриста в отрасли """

        mediator = get_object_or_404(self.queryset, **kwargs)
        filterer = IndustryContactsSearchFilter()
        type_filterer = IndustryContactsTypeFilter()

        invites = Invite.get_pending_mediator_invites_for_industry_contacts(
            mediator
        )
        invites = filterer.filter_queryset(request, invites, None)
        invites = type_filterer.filter_contact_type(request, invites)
        contacts = mediator.industry_contacts.all()
        contacts = filterer.filter_queryset(request, contacts, None)
        contacts = type_filterer.filter_contact_type(request, contacts)

        industry_contacts = set(invites) | set(contacts)

        page = self.paginate_queryset(queryset=list(industry_contacts))
        ordering_fields = request.GET.getlist('ordering', [])
        if page is not None:
            serializer = IndustryContactSerializer(page, many=True)
        else:
            serializer = IndustryContactSerializer(
                industry_contacts,
                many=True
            )

        data = serializer.data
        for field in ordering_fields:
            reverse = False
            if field.startswith('-'):
                reverse = True
                field = field[1:]
            data = sorted(
                data,
                key=lambda k: (k[field] is not None, k[field]),
                reverse=reverse
            )

        if page is not None:
            return self.paginator.get_paginated_response(data)
        else:
            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['GET'])
    def industry_contact_detail(self, request, *args, **kwargs):
        """ Контактные данные для возврата в адвокатскую контору """
        self.get_object()
        user_id = request.query_params.get('user_id', None)
        if not user_id:
            return Http404('Invalid request data.')

        try:
            contact = get_user_model().objects.get(pk=user_id)
        except Exception:
            raise Http404('No %s matches the given query.' %
                          get_user_model()._meta.object_name)


        serializer = IndustryContactMediatorDetails(contact)

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'])
    def add_industrial_contact(self, request, *args, **kwargs):
        """ Добавляет новые производственные контакты """

        mediator = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            raise Http404('Invalid request data.')

        try:
            new_industry_contact = get_user_model().objects.get(pk=user_id)
            #if new_industry_contact.user_type == 'client':
            #    raise Http404('Invalid request data.')
            mediator.industry_contacts.add(
                new_industry_contact
            )
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except get_user_model().DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False}
            )

    @action(detail=True, methods=['DELETE'])
    def remove_industrial_contact(self, request, *args, **kwargs):
        """ Устраняет промышленный контакт """

        mediator = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Http404('Invalid request data.')

        try:
            mediator.industry_contacts.remove(
                get_user_model().objects.get(pk=user_id)
            )
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except get_user_model().DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False}
            )

    @action(detail=True, methods=['POST'])
    def add_contact(self, request, *args, **kwargs):
        """ Добавить клиента в качестве контакта """

        mediator = self.get_object()
        client_id = request.data.get("client", None)
        try:
            client = Client.objects.get(pk=client_id)
            Lead.objects.get_or_create(mediator=mediator, client=client)
            return Response(
                status=status.HTTP_200_OK,
                data={"success": True}
            )
        except Client.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "success": False,
                    "detail": "Client profile does not exist"
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

    @action(detail=True, methods=['PUT'])
    def update_contact(self, request, *args, **kwargs):
        # Проверка разрешений адвоката.
        # адвокат = self.get_object()

        object_map = {
            True: Invite,
            False: Client
        }
        from apps.users.api.serializers import (
            UpdateClientSerializer,
            UpdateInviteSerializer,
        )

        serializer_map = {
            True: UpdateInviteSerializer,
            False: UpdateClientSerializer
        }
        is_pending = request.data.get('is_pending', False)

        contact_model = object_map.get(is_pending)
        contact_id = request.data.get('contact_id')

        try:
            contact = get_object_or_404(contact_model, **{'pk': contact_id})
        except Exception:
            raise Http404('Invalid contact details.')

        if not contact:
            raise Http404('Invalid contact details.')

        serializer_class = serializer_map[is_pending]
        serializer = serializer_class(
            instance=contact,
            data=request.data['contact_data'],
            context={'request': request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            LeadAndClientSerializer(
                updated_instance, context={'request': request}
            ).data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def engagements(self, request, **kwargs):
        """View for getting mediator engagements."""

        mediator = self.request.user.mediator

        proposals = Proposal.objects.filter(mediator=mediator).select_related(
            'mediator',
            'mediator__user',
            'currency'
        ).prefetch_related(
            'post',
            'post__practice_area',
            'post__client',
        )

        status_required = request.GET.get('status')
        is_hidden_for_mediator = \
            request.query_params.get('is_hidden_for_mediator')
        if status_required:
            proposals = proposals.filter(status=status_required)
        else:
            is_active = request.GET.get('is_active')
            if is_active == '1':
                proposals = proposals.filter(
                    post__status=PostedMatter.STATUS_ACTIVE
                )
            elif is_active == '0':
                proposals = proposals.exclude(
                    post__status=PostedMatter.STATUS_ACTIVE
                )
        if is_hidden_for_mediator == 'true':
            proposals = proposals.filter(is_hidden_for_mediator=True)
        elif is_hidden_for_mediator == 'false':
            proposals = proposals.filter(is_hidden_for_mediator=False)
        page = self.paginate_queryset(proposals)
        if page is not None:
            serializer = MediatorProposalSerializer(page, many=True)
            return self.paginator.get_paginated_response(data=serializer.data)

        serializer = MediatorProposalSerializer(mediator)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def get_all_contacts(self, request, *args, **kwargs):
        mediator = self.get_object()
        industry_contacts = set(
            mediator.industry_contacts.values_list(
                'id', flat=True
            )
        )
        opportunities = set(
            mediator.opportunities.values_list(
                'client__user', flat=True
            )
        )
        leads = set(
            mediator.leads.values_list(
                'client__user',
                flat=True
            )
        )
        clients = set(
            mediator.matters.values_list(
                'client__user',
                flat=True
            )
        )
        contacts = industry_contacts | opportunities | leads | clients
        mediator_contacts = get_user_model().objects.filter(
            id__in=contacts
        )

        page = self.paginate_queryset(mediator_contacts)
        if page is not None:
            serializer = serializers.AppUserShortSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.AppUserShortSerializer(
            mediator_contacts,
            many=True
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['POST'], detail=True)
    def leave_enterprise(self, request, *args, **kwargs):
        try:
            mediator = self.get_object()
            enterprise_id = request.data.get('enterprise', None)
            enterprise = Enterprise.objects.get(pk=enterprise_id)
            if mediator.enterprise != enterprise:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "success": False,
                        "detail": "You are not member of "
                                  "enterprise with id={}".format(enterprise_id)
                    }
                )
            mediator.enterprise = None
            mediator.save()
            EnterpriseMembers.objects.filter(
                enterprise=enterprise,
                user=request.user
            ).delete()
            return Response(
                data={"success": True},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"success": False, "detail": str(e)}
            )


class CurrentMediatorView(
    UserAgentLoggingMixin,
    generics.UpdateAPIView,
    generics.RetrieveAPIView,
    generics.GenericAPIView
):
    """Retrieve and update user's mediator profile.

    Accepts GET, PUT and PATCH methods.
    Read-only fields:
        * first_name
        * last_name
        * user
        * is_verified
        * specialities_data
        * fee_types_data 
    """
    serializer_class = serializers.CurrentMediatorSerializer

    permission_classes = (
        IsAuthenticated,
        permissions.IsMediatorFreeAccess,
    )
    queryset = Mediator.objects.real_users().\
        select_related(
        'user',
        'fee_currency',
    ).prefetch_related(
        'followers',
        'practice_jurisdictions',
        'education',
        'education__university',
        'user__specialities',
        'firm_locations',
        'firm_locations__country',
        'firm_locations__state',
        'firm_locations__city',
        'firm_locations__city__region',
        'practice_jurisdictions',
        'practice_jurisdictions__country',
        'practice_jurisdictions__state',
        'fee_types',
        'appointment_type',
        'payment_type',
        'spoken_language',
        'registration_attachments',
    )

    def get_object(self):
        """Get user's Mediator profile."""
        return self.queryset.get(user=self.request.user)

    def get_serializer_class(self):
        """Return serializer for update on `PUT` or `PATCH` requests.

        Can't use ActionSerializerMixin since it's not view-set.

        """
        if self.request.method in ('PUT', 'PATCH',):
            return serializers.UpdateMediatorSerializer
        return super().get_serializer_class()


class CurrentMediatorActionsViewSet(BaseViewSet):
    """View for retrieving different current Mediator related info.

    As far as original `CurrentMediatorView` is a simple generics view we
    couldn't easily add different named actions to it only `get`, `put` and etc
    methods.

    This viewset solves the issue and allows to define actions with different
    names. So all related to current mediator actions can be placed here.

    """
    permission_classes = (
        IsAuthenticated,
        permissions.IsMediatorHasActiveSubscription,
    )
    base_filter_backends = None
    pagination_class = None

    @action(methods=['get'], url_path='statistics/current', detail=False)
    def current_statistics(self, request, *args, **kwargs):
        """Get mediator current statistics.

        Current mediator statistics is a statistics for current period of time.
        Current mediator statistics includes:
            Count of active leads,
            Count of active matters,
            Count of documents,
            Count of opportunities

        """
        return Response(
            data=services.get_mediator_statistics(request.user.mediator),
        )

    @action(methods=['get'], url_path='statistics/period', detail=False)
    def period_statistics(self, request, *args, **kwargs):
        """Get mediator statistics for for time period.

        Period mediator statistics is a statistics for selected period of time,
        where some of them (time_billed for now) divided by time frame.
        Period mediator statistics includes:
            Amount of billed time (divided by `time frame`),
            Count of active leads for period of time,
            Count of active matters for period of time,
            Count of opportunities for period of time,
            Count of converted leads for period of time

        """
        serializer = serializers.MediatorPeriodStatsQueryParamsSerializer(
            data=request.query_params
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            data=services.get_mediator_period_statistic(
                request.user.mediator, **serializer.data
            )
        )
