from django.db.models import Count
from rest_framework import serializers
from libs.django_cities_light.api.serializers import (
    CitySerializer,
    CountrySerializer,
    RegionSerializer,
)
from apps.business.models.matter import Matter
from apps.core.api.serializers import BaseSerializer
from apps.documents.api.serializers import DocumentOverviewSerializer
from apps.documents.models import Document
from apps.social.api.serializers import ChatOverviewSerializer
from apps.social.models import Chats
from apps.users.api.serializers import (
    AppUserShortSerializer,
    MediatorSerializer,
    EnterpriseSerializer,
    FeeKindSerializer,
    SpecialitySerializer,
)
from apps.users.models import Mediator, Client, Enterprise, Invite
from ... import models
from ...models import Invoice
from .invoices import InvoiceClientOverviewSerializer
from .links import ShortActivitySerializer


class LeadOverViewSerializer(BaseSerializer):
    """ Сериализует сведения об ограниченных потенциальных клиентах
    для панели управления адвокатом и чата. """
    name = serializers.CharField(
        source='client.full_name'
    )
    avatar = serializers.FileField(
        source="client.user.avatar"
    )

    class Meta:
        model = models.Lead
        fields = (
            'id',
            'name',
            'priority',
            'chat_channel',
            'avatar'
        )


class LeadAndClientSerializer(serializers.Serializer):
    """ Упорядочивает приглашения, лиды и клиентов для адвоката. """
    id = serializers.CharField(
        source='pk',
        read_only=True
    )
    first_name = serializers.SerializerMethodField(
        read_only=True
    )
    middle_name = serializers.SerializerMethodField(
        read_only=True
    )
    last_name = serializers.SerializerMethodField(
        read_only=True
    )
    phone = serializers.SerializerMethodField(
        read_only=True
    )
    avatar = serializers.CharField(
        source='user.avatar_url',
        read_only=True,
        allow_null=True,
        default=None
    )
    job = serializers.SerializerMethodField(
        read_only=True
    )
    company = serializers.CharField(
        source='organization_name',
        read_only=True
    )
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CitySerializer(source='city', read_only=True)
    address = serializers.SerializerMethodField(
        read_only=True
    )
    zipcode = serializers.CharField(source='zip_code', read_only=True)
    note = serializers.CharField(read_only=True)
    type = serializers.SerializerMethodField(
        read_only=True
    )
    email = serializers.SerializerMethodField(
        read_only=True
    )
    matters_count = serializers.SerializerMethodField(
        read_only=True
    )
    is_pending = serializers.SerializerMethodField(
        read_only=True
    )

    def get_first_name(self, obj):
        if isinstance(obj, Invite):
            return obj.first_name
        else:
            return obj.user.first_name

    def get_middle_name(self, obj):
        if isinstance(obj, Invite):
            return obj.middle_name
        else:
            return obj.user.middle_name

    def get_last_name(self, obj):
        if isinstance(obj, Invite):
            return obj.last_name
        else:
            return obj.user.last_name

    def get_email(self, obj):
        return obj.email if isinstance(obj, Invite) else obj.user.email

    def get_phone(self, obj):
        return obj.phone if isinstance(obj, Invite) else obj.user.phone

    def get_job(self, obj):
        return obj.job if isinstance(obj, Client) else obj.role

    def get_type(self, obj):
        user = self.context['request'].user
        if user.is_mediator and obj.matters.count():
            return 'client'
        elif not isinstance(
            obj, Invite
        ) and obj.leads.count():
            return 'client'
        elif isinstance(obj, Invite):
            return obj.client_type
        else:
            return 'lead'

    def get_is_pending(self, obj):
        return isinstance(obj, Invite)

    def get_matters_count(self, obj):
        return obj.matters.count()

    def get_address(self, obj):
        return obj.address1 if isinstance(obj, Client) else obj.address

    class Meta:
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'phone',
            'avatar',
            'job',
            'company',
            'type',
            'email',
            'note',
            'country_data',
            'state_data',
            'city_data',
            'address',
            'zipcode',
            'is_pending'
            'matters_count',
        ]


class OpportunityOverViewSerializer(BaseSerializer):
    """ Сериализует сведения об ограниченных возможностях для панели 
    управления адвоката и чата. """
    name = serializers.CharField(
        source='client.full_name'
    )
    avatar = serializers.FileField(
        source="client.user.avatar"
    )

    class Meta:
        model = models.Opportunity
        fields = (
            'id',
            'name',
            'priority',
            'chat_channel',
            'avatar'
        )


class MatterShortOverviewSerializer(BaseSerializer):
    """ Сериализует ограниченный материал
    подробная информация для панели управления адвокатом. """
    client_name = serializers.CharField(
        source='client.full_name', read_only=True
    )
    principle_name = serializers.CharField(
        source='mediator.full_name', read_only=True
    )
    client_avatar = serializers.SerializerMethodField(
        read_only=True
    )
    principle_avatar = serializers.FileField(
        source='mediator.user.avatar', read_only=True
    )
    practice_area = serializers.CharField(
        source='speciality.title',
        allow_null=True,
        allow_blank=True,
        read_only=True
    )
    fee_type = serializers.CharField(
        source='fee_type.title', read_only=True
    )

    def get_client_avatar(self, obj):
        if obj.client:
            if obj.client.user.avatar == '[]' or obj.client.user.avatar == '':
                return None
            return obj.client.user.avatar
        else:
            return None

    class Meta:
        model = models.Matter
        fields = [
            'id',
            'title',
            'client',
            'client_name',
            'client_avatar',
            'practice_area',
            'principle_avatar',
            'principle_name',
            'fee_type',
            'created'
        ]


class MatterOverviewClientDashboardSerializer(BaseSerializer):
    """ Сериализует вопросы для клиентской панели мониторинга. """
    mediator_id = serializers.IntegerField(
        source='mediator.pk'
    )
    mediator_name = serializers.CharField(
        source='mediator.user.full_name'
    )
    mediator_avatar = serializers.FileField(
        source='mediator.user.avatar'
    )
    mediator_email = serializers.EmailField(
        source='mediator.user.email'
    )
    due_amount = serializers.SerializerMethodField(
        read_only=True
    )
    shared_with_data = AppUserShortSerializer(
        source='shared_with',
        many=True,
        read_only=True
    )
    speciality_data = SpecialitySerializer(
        source='speciality', read_only=True
    )
    rate_type = FeeKindSerializer(
        source='fee_type',
        read_only=True
    )
    stage = serializers.SerializerMethodField(
        read_only=True
    )
    unread_message_count = serializers.SerializerMethodField(read_only=True)
    unread_document_count = serializers.SerializerMethodField(read_only=True)

    def get_due_amount(self, obj):
        """ Рассчитывает и возвращает причитающуюся сумму за определенный период. """
        invoices = obj.invoices.prefetch_related(
            'billing_items'
        ).exclude(
            payment_status='paid'
        )
        return sum([invoice.fees_earned for invoice in invoices])

    def get_unread_message_count(self, obj):
        """ Возвращает количество непрочитанных сообщений ."""
        posts = obj.posts.prefetch_related('comments')
        unread_comment_count = sum(
            [post.unread_comment_by_client_count for post in posts]
        )
        return unread_comment_count

    def get_unread_document_count(self, obj):
        """ Возвращает количество непрочитанных документов. """
        count = 0
        for doc in obj.documents.all():
            if not doc.seen:
                count += 1
        for folder in obj.folders.all():
            if not folder.seen:
                count += 1
        return count

    def get_stage(self, obj):
        return obj.stage.title if obj.stage else None

    class Meta:
        model = models.Matter
        fields = [
            'id',
            'title',
            'description',
            'start_date',
            'mediator_id',
            'mediator_name',
            'mediator_email',
            'mediator_avatar',
            'shared_with_data',
            'speciality_data',
            'rate_type',
            'unread_document_count',
            'unread_message_count',
            'due_amount',
            'status',
            'stage',
            'created'
        ]


class MediatorDetailedOverviewSerializer(MediatorSerializer):
    """
    Сериализирует детали для панели управления адвоката
    Поля:
         open_matters: Список сериализованных активных дел
         адвоката, а также активные дела, которыми поделился с адвокатом.
         выставление счетов: Dict, содержащий сводку счетов для адвоката.
    """
    open_matters = serializers.SerializerMethodField(
        read_only=True
    )
    open_matters_count = serializers.SerializerMethodField(
        read_only=True
    )
    billing = serializers.SerializerMethodField(
        read_only=True
    )
    chats = serializers.SerializerMethodField(
        read_only=True
    )
    activities = serializers.SerializerMethodField(
        read_only=True
    )

    def get_open_matters(self, obj):
        """
        Возвращается:
            Список серийных адвокатских дел
            а также дела, которыми поделились с адвокатом
        """
        matters = obj.matters.all()[:2]
        return MatterShortOverviewSerializer(
            matters,
            read_only=True,
            many=True
        ).data

    def get_open_matters_count(self, obj):
        """
        Количество открытых дел
        """
        return obj.matters.count()

    def get_billing(self, obj):
        """
        Returns:
            Сериализуем платежные реквизиты адвоката.
        """
        paid = 0
        overdue = 0
        un_billed = 0
        unpaid = 0
        items = obj.user.billing_item.all()
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) == 0:
                un_billed += item.fee
            elif invs[0].status == Invoice.INVOICE_STATUS_OVERDUE:
                overdue += item.fee
            elif invs[0].status == Invoice.INVOICE_STATUS_PAID:
                paid += item.fee
            else:
                unpaid += item.fee
        return {
            'paid': paid,
            'overdue': overdue,
            'un_billed': un_billed,
            'unpaid': unpaid
        }

    def get_chats(self, obj):
        """
            Сериализуем id чата адвоката
            с лидами и возможностями.
        """
        chats = obj.user.chats.all()
        data = ChatOverviewSerializer(
            chats,
            context={'request': self.context['request']},
            many=True
        ).data
        result = []
        for obj in data:
            if obj['chat_type'] != 'network':
                result.append(obj)
        return result

    def get_activities(self, obj):
        """
        Сериализуем деятельность адвоката
        """
        return ShortActivitySerializer(
            obj.user.activities.order_by('-modified')[:2],
            many=True,
            read_only=True
        ).data

    class Meta:
        model = Mediator
        fields = [
            'open_matters',
            'open_matters_count',
            'billing',
            'chats',
            'activities'
        ]


class ClientOverviewSerializer(BaseSerializer):
    """ Сериализуем подробная информация для клиентской панели мониторинга. """
    recent_matters = serializers.SerializerMethodField(
        read_only=True
    )
    recent_documents = serializers.SerializerMethodField(
        read_only=True
    )
    upcoming_bills = serializers.SerializerMethodField(
        read_only=True
    )
    recent_activities = serializers.SerializerMethodField(
        read_only=True
    )

    def get_recent_matters(self, obj):
        user = self.context['request'].user
        if user.is_mediator:
            return MatterOverviewClientDashboardSerializer(
                obj.matters.filter(mediator=user.mediator).select_related(
                    'mediator',
                    'mediator__user',
                    'stage',
                    'speciality',
                    'fee_type',
                ).prefetch_related(
                    'shared_with',
                    'documents',
                    'folders',
                ).order_by('-created')[:2],
                many=True
            ).data
        else:
            return MatterOverviewClientDashboardSerializer(
                obj.matters.select_related(
                    'mediator',
                    'mediator__user',
                    'stage',
                    'speciality',
                    'fee_type',
                ).prefetch_related(
                    'shared_with',
                    'documents',
                    'folders',
                ).order_by('-created')[:2],
                many=True
            ).data

    def get_recent_documents(self, obj):
        documents = Document.client_documents(obj).select_related(
            'created_by'
        ).order_by('-created')[:2]
        return DocumentOverviewSerializer(
            documents,
            many=True
        ).data

    def get_upcoming_bills(self, obj):
        invoices = Invoice.client_upcoming_invoices(obj).select_related(
            'created_by',
            'created_by__mediator',
        ).prefetch_related(
            'billing_items'
        ).order_by('-created')[:2]
        return InvoiceClientOverviewSerializer(
            invoices,
            many=True
        ).data

    def get_recent_activities(self, obj):
        return ShortActivitySerializer(
            obj.user.activities.all()[:2],
            many=True,
            read_only=True
        ).data

    class Meta:
        model = Client
        fields = [
            'recent_matters',
            'recent_documents',
            'upcoming_bills',
            'recent_activities'
        ]


class EnterpriseDetailedOverviewSerializer(EnterpriseSerializer):
    """
    Сериализуем подробная информация для корпоративной панели мониторинга
    Поля:
        open_matters: Список сериализованных активных дел, совместно используемых предприятием.
        billing: Диктант, содержащий сводку выставления счетов для предприятия
        chats: Список сериализованных активных чатов
        activities: Список сериализованных видов деятельности
    """
    open_matters = serializers.SerializerMethodField(
        read_only=True
    )
    billing = serializers.SerializerMethodField(
        read_only=True
    )
    chats = serializers.SerializerMethodField(
        read_only=True
    )
    activities = serializers.SerializerMethodField(
        read_only=True
    )

    def get_open_matters(self, obj):
        """
            Список упорядоченных дел, общий для фирмы
        """
        user = self.context['request'].user
        matters = Matter.objects.filter(shared_with__in=[user.pk])
        return MatterShortOverviewSerializer(
            matters,
            read_only=True,
            many=True
        ).data

    def get_billing(self, obj):
        """
            Сериализуем billing детали для фирмы.
        """
        paid = 0
        overdue = 0
        un_billed = 0
        unpaid = 0
        items = obj.user.billing_item.prefetch_related(
            'billing_items_invoices'
        )
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) == 0:
                un_billed += item.fee
            elif invs[0].status == Invoice.INVOICE_STATUS_OVERDUE:
                overdue += item.fee
            elif invs[0].status == Invoice.INVOICE_STATUS_PAID:
                paid += item.fee
            else:
                unpaid += item.fee
        return {
            'paid': paid,
            'overdue': overdue,
            'un_billed': un_billed,
            'unpaid': unpaid
        }

    def get_chats(self, obj):
        """
            Сериализуем IDs чатов фирмы
            с лидами и возможностями.
        """
        chats = Chats.objects.annotate(msg_count=Count('messages')).filter(
            msg_count__gt=0
        ).prefetch_related(
            'messages', 'participants'
        )
        data = ChatOverviewSerializer(
            chats,
            context={'request': self.context['request']},
            many=True
        ).data
        result = []
        for obj in data:
            if obj['chat_type'] != 'network':
                result.append(obj)
        return result

    def get_activities(self, obj):
        """
            Сериализуем активности для фирмы
        """
        return ShortActivitySerializer(
            obj.user.activities.all()[:2],
            many=True,
            read_only=True
        ).data

    class Meta:
        model = Enterprise
        fields = (
            'open_matters',
            'billing',
            'chats',
            'activities'
        )
