from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from libs.api.serializers.fields import DateTimeFieldWithTZ
from libs.django_cities_light.api.serializers import (
    CitySerializer,
    CityShortSerializer,
    CountrySerializer,
    RegionSerializer,
)
from apps.business.models.invoices import Invoice
from apps.users.models import AppUser, FeeKind
from ....business import models
from ....core.api.serializers import BaseSerializer
from ....documents.models import Document
from ....esign.adapters import DocuSignAdapter
from ....esign.api.serializers import (
    EnvelopeShortSerializer,
    ESignDocumentSerializer,
)
from ....esign.models import Envelope
from ....esign.services import get_matter_initial_envelope
from ....users.api.serializers import (
    AppUserShortSerializer,
    AppUserWithoutTypeSerializer,
    MediatorShortSerializer,
    ClientDetailInfoSerializer,
    ClientInfoSerializer,
    CurrenciesSerializer,
    FeeKindSerializer,
    InviteSerializer,
    SpecialitySerializer,
)
from ....users.api.serializers.mediators import MediatorOverviewSerializer
from ...signals import matter_stage_update, new_lead, new_matter
from .extra import ReferralSerializer, StageSerializer


class ShortLeadSerializer(BaseSerializer):
    """ Короткий сериализатор для модели Lead """

    class Meta:
        model = models.Lead
        fields = (
            'id',
            'post',
            'priority',
            'chat_channel',
        )


class LeadSerializer(ShortLeadSerializer):
    """ сериализатор для модели Lead """
    client_data = ClientInfoSerializer(
        source='client', read_only=True
    )
    mediator_data = MediatorShortSerializer(
        source='mediator', read_only=True
    )

    class Meta:
        model = models.Lead
        fields = (
            'id',
            'post',
            'client',
            'client_data',
            'mediator',
            'mediator_data',
            'priority',
            'status',
            'chat_channel',
            'created',
            'modified',
        )
        read_only_fields = (
            # должно быть сгенерировано приложением
            'chat_channel',
            'status',
            'created',
            'modified',
        )

    def create(self, validated_data):
        """ Отправьте уведомление о новом лиде адвокату или клиенту. """
        lead = super().create(validated_data)
        new_lead.send(
            sender=models.Lead,
            instance=lead,
            created_by=self.user,
            user=self.user
        )
        return lead

    def validate(self, attrs):
        """
        Установите `адвоката` или `клиента` ведущего в зависимости от пользователя из запроса.
        """
        user = self.user
        if user:
            if user.is_mediator:
                attrs['mediator'] = user.mediator
            if user.is_client:
                attrs['client'] = user.client

        # TODO: установите "клиент" из "темы", если тема будет установлена
        # когда будут реализованы "форумы")
        return super().validate(attrs)


class OpportunitySerializer(BaseSerializer):
    """ сериализатор для модели Opportunity """
    client_data = ClientInfoSerializer(
        source='client', read_only=True
    )
    mediator_data = MediatorShortSerializer(
        source='mediator', read_only=True
    )

    class Meta:
        model = models.Opportunity
        fields = (
            'id',
            'client',
            'client_data',
            'mediator',
            'mediator_data',
            'priority',
            'chat_channel',
            'created',
            'modified',
        )
        read_only_fields = (
            # должно быть сгенерировано приложением
            'chat_channel',
            'created',
            'modified',
        )


class UpdateLeadSerializer(LeadSerializer):
    """ Ведущий сериализатор обновлений. """

    class Meta(LeadSerializer.Meta):
        read_only_fields = LeadSerializer.Meta.read_only_fields + (
            'post',
            'client',
            'mediator'
        )


class ShortMatterSerializer(BaseSerializer):
    """ Короткий сериализатор для модели Matter """

    class Meta:
        model = models.Matter
        fields = (
            'id',
            'code',
            'title',
            'description',
        )


class ActivityShortSerializer(BaseSerializer):
    """ сериализатор для модели `Activity` """

    user_data = AppUserWithoutTypeSerializer(source='user', read_only=True)

    class Meta:
        model = models.Activity
        fields = (
            'id',
            'title',
            'user_data',
            'created',
            'modified',
        )


class MatterSerializer(BaseSerializer):
    """ сериализатор для модели Matter """
    description = serializers.CharField(allow_blank=True, required=False)
    client_data = ClientDetailInfoSerializer(source='client', read_only=True)
    mediator_data = MediatorOverviewSerializer(
        source='mediator', read_only=True
    )
    stage_data = StageSerializer(source='stage', read_only=True)
    country_data = CountrySerializer(source='country', read_only=True)
    state_data = RegionSerializer(source='state', read_only=True)
    city_data = CityShortSerializer(source='city', read_only=True)
    city = CitySerializer(write_only=True, required=False, allow_null=True)
    referral_data = ReferralSerializer(source='referral', read_only=True)
    referral_request = serializers.SerializerMethodField(
        help_text='Matter is referred by mediator'
    )
    referral_pending = serializers.SerializerMethodField(
        help_text='Referred matter to mediator'
    )
    fees_earned = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    esign_documents = ESignDocumentSerializer(
        many=True,
        write_only=True,
        allow_empty=True,
        allow_null=True,
        required=False
    )
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=AppUser.objects.all(),
        many=True,
        allow_empty=True,
        required=False
    )
    shared_with_data = AppUserShortSerializer(
        source='shared_with',
        many=True,
        read_only=True
    )
    is_billable = serializers.BooleanField()
    is_shared = serializers.SerializerMethodField()
    envelope_data = EnvelopeShortSerializer(read_only=True)
    speciality_data = SpecialitySerializer(
        source='speciality', read_only=True
    )
    currency_data = CurrenciesSerializer(
        source='currency',
        required=False
    )
    fee_type = serializers.PrimaryKeyRelatedField(
        queryset=FeeKind.objects.all(),
        required=False
    )
    rate_type = FeeKindSerializer(
        source='fee_type',
        read_only=True
    )

    invite_data = InviteSerializer(source='invite', read_only=True)

    due_amount = serializers.SerializerMethodField(read_only=True)
    unread_message_count = serializers.SerializerMethodField(read_only=True)
    unread_document_count = serializers.SerializerMethodField(read_only=True)
    referral_ignore_mediator_data = MediatorOverviewSerializer(
        source='referral_ignore_mediator', read_only=True
    )

    class Meta:
        model = models.Matter
        fields = (
            'id',
            'lead',
            'client',
            'client_data',
            'mediator',
            'mediator_data',
            'code',
            'title',
            'description',
            'fees_earned',
            'rate_type',
            'rate',
            'country',
            'country_data',
            'speciality',
            'speciality_data',
            'state',
            'state_data',
            'city',
            'city_data',
            'status',
            'stage',
            'stage_data',
            'referral',
            'referral_data',
            'referral_request',
            'referral_pending',
            'referral_ignored',
            'referral_ignore_mediator_data',
            'completed',
            'esign_documents',
            'shared_with',
            'shared_with_data',
            'is_shared',
            'envelope_data',
            'created',
            'modified',
            'currency',
            'currency_data',
            'start_date',
            'close_date',
            'is_billable',
            'fee_type',
            'fee_note',
            'invite',
            'invite_data',
            'unread_document_count',
            'unread_message_count',
            'due_amount',
        )
        read_only_fields = (
            # адвокат взят из запроса
            'mediator',
            # должно быть изменено отдельными методами API
            'status',
            # изменяется приложением при установке статуса `завершено`
            'completed',
            'fees_earned',
            'created',
            'modified',
            'currency_data',
            'is_billable',
            'invite_data'
        )
        extra_kwargs = {
            'description': {
                'required': False
            },
            'rate': {
                'required': False
            },
            'fee_note': {
                'allow_blank': True
            }
        }
        relations = (
            'shared_with'
        )

    def get_is_shared(self, obj: models.Matter) -> bool:
        """ Получите `is_shared` для текущего пользователя. """
        if not self.user:
            return False
        return obj.is_shared_for_user(self.user)

    def get_referral_request(self, obj: models.Matter):
        """ Получите, если вопрос передан по """
        if obj.referral is None:
            return False
        return self.user == obj.referral.mediator.user

    def get_referral_pending(self, obj: models.Matter):
        """ Получите, если вопрос передан по """
        if obj.referral is None:
            return False
        return obj.mediator.user == self.user

    def get_unread_message_count(self, obj):
        """ Возвращает количество непрочитанных сообщений. """
        count = 0
        for post in obj.posts.all():
            if self.user in post.participants.all() and \
                    not post.seen_by_client:
                count += 1
        return count

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

    def get_due_amount(self, obj):
        """ Рассчитывает и возвращает причитающуюся сумму за определенный период. """
        amount = 0
        for invoice in obj.invoices.all():
            if invoice.payment_status != 'paid':
                amount += invoice.fees_earned
        return amount

    def validate(self, attrs):
        """
        Установите значение `адвокат` из запроса и "клиент" из `ведущий`
        (если он существует) и затем проверьте подготовленный экземпляр.
        """
        if attrs.get('is_billable') and attrs.get('fee_type', None) is None:
            raise serializers.ValidationError(
                "Fee type is required"
            )
        elif attrs.get('is_billable') and attrs.get('fee_type').pk == 1:
            if attrs.get('rate', None) is None or \
                    attrs.get('currency', None) is None:
                raise serializers.ValidationError(
                    "Rate is required and Currency is required"
                )
        elif attrs.get('is_billable') and attrs.get('fee_type').pk == 2:
            if attrs.get('rate', None) is None:
                raise serializers.ValidationError(
                    "Rate is required"
                )
        elif attrs.get('is_billable') and attrs.get('fee_type').pk == 4:
            if attrs.get('fee_note', "") == "":
                raise serializers.ValidationError(
                    "Fee note is required"
                )
        elif attrs.get('is_billable') and attrs.get('fee_type').pk == 5:
            attrs['rate'] = 0
        request, view = self.context.get('request'), self.context.get('view')
        if attrs.get('fee_type', None) and attrs.get('fee_type').pk == 3:
            attrs['rate'] = request.user.mediator.fee_rate
        # установите значение из запроса только для метода API `create`
        if request and view.action == 'create':
            attrs['mediator'] = request.user.mediator

        # установите `client` из lead, если он установлен только для метода API `create`
        if view.action == 'create' and attrs.get('lead'):
            attrs['client'] = attrs['lead'].client
        #if view.action == 'create' and attrs.get('client', None) is None and \
        #        attrs.get('invite', None) is None:
        #    raise ValidationError('Either client or invite should be provided')
        return super().validate(attrs)

    def to_representation(self, instance):
        """ Добавьте `исходные` данные matter. """
        data = super().to_representation(instance)

        # не используйте `get_matter_initial_envelope` по соображениям производительности
        envelopes = instance.envelopes.all()
        envelope = envelopes[0] if envelopes.exists() else None
        data['envelope_data'] = self.fields['envelope_data'] \
            .to_representation(envelope) if envelope else None

        return data

    def create(self, validated_data):
        """ Создайте дело с документами для электронной подписи. """
        esign_documents = validated_data.pop('esign_documents', None)
        instance = super().create(validated_data)
        new_matter.send(
            sender=models.Matter, instance=instance, user=self.user
        )
        if not esign_documents:
            return instance

        # подготовьте Sign-конверт с документами в DB и DocuSign
        adapter = DocuSignAdapter(user=self.user)
        adapter.create_envelope(
            matter=instance,
            documents=[doc['file'] for doc in esign_documents],
            type=Envelope.TYPE_INITIAL
        )
        return instance


class MatterDetailSerializer(MatterSerializer):
    attachment = serializers.SerializerMethodField(read_only=True)
    activities = serializers.SerializerMethodField(read_only=True)
    unread_comment_count = serializers.SerializerMethodField(read_only=True)
    total_amount = serializers.SerializerMethodField(read_only=True)
    paid = serializers.SerializerMethodField(read_only=True)
    unpaid = serializers.SerializerMethodField(read_only=True)
    overdue = serializers.SerializerMethodField(read_only=True)
    unbilled = serializers.SerializerMethodField(read_only=True)
    invoices = serializers.SerializerMethodField(read_only=True)

    class Meta(MatterSerializer.Meta):
        fields = MatterSerializer.Meta.fields + (
            'invoices',
            'activities',
            'attachment',
            'unread_comment_count',
            'total_amount',
            'paid',
            'unpaid',
            'overdue',
            'unbilled'
        )

    def get_activities(self, obj: models.Matter):
        """ Получить информацию о последних действиях """
        if not self.context['request'].user.is_client:
            activities = obj.activities.select_related('user').filter(
                user=self.context['request'].user
            )
        else:
            activities = obj.activities.all()
        return ActivityShortSerializer(
            activities,
            many=True,
            read_only=True
        ).data

    def get_attachment(self, obj):
        """ Возвращает вложения, принадлежащие matter """
        return MatterDocumentSerializer(
            obj.documents.all(),
            read_only=True,
            many=True
        ).data

    def get_unread_comment_count(self, obj):
        """ Возвращает общее количество непрочитанных комментариев. """
        posts = obj.posts.filter(
            participants__in=[self.context['request'].user]
        )
        unread_comment_count = sum(
            [post.unread_comment_count for post in posts]
        )
        return unread_comment_count

    def get_total_amount(self, obj):
        items = obj.billing_item.all()
        amount = 0
        for item in items:
            amount += item.fee
        return amount

    def get_paid(self, obj):
        items = obj.billing_item.all()
        amount = 0
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) > 0 and invs[0].status == Invoice.INVOICE_STATUS_PAID:
                amount += item.fee
        return amount

    def get_unpaid(self, obj):
        items = obj.billing_item.all()
        amount = 0
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) > 0 and invs[0].status != Invoice.INVOICE_STATUS_PAID:
                amount += item.fee
        return amount

    def get_overdue(self, obj):
        items = obj.billing_item.all()
        amount = 0
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) > 0 and invs[0].status == \
                    Invoice.INVOICE_STATUS_OVERDUE:
                amount += item.fee
        return amount

    def get_unbilled(self, obj):
        items = obj.billing_item.all()
        amount = 0
        for item in items:
            invs = item.billing_items_invoices.all()
            if len(invs) == 0:
                amount += item.fee
        return amount

    def get_invoices(self, obj):
        """ Возвращает краткую информацию о статусе счета-фактуры """
        from .invoices import InvoiceShortSerializer
        return InvoiceShortSerializer(
            obj.invoices.all(),
            read_only=True,
            many=True
        ).data


class MatterOverviewSerializer(BaseSerializer):
    """ Сериализует ограниченные сведения только для общего ознакомления. """
    mediator = MediatorOverviewSerializer(
        read_only=True
    )
    stage = serializers.SerializerMethodField(
        read_only=True
    )
    shared = AppUserShortSerializer(
        source='shared_with',
        many=True,
        read_only=True
    )
    rate = FeeKindSerializer(
        source='fee_type',
        read_only=True
    )
    amount_paid = serializers.SerializerMethodField(
        read_only=True
    )
    total_balance = serializers.SerializerMethodField(
        read_only=True
    )
    due_amount = serializers.SerializerMethodField(
        read_only=True
    )
    due_date = serializers.SerializerMethodField(
        read_only=True
    )
    activity = serializers.SerializerMethodField(
        read_only=True
    )

    def get_due_amount(self, obj):
        invoices = obj.invoices.prefetch_related(
            'billing_items'
        ).exclude(
            payment_status='paid'
        )
        return sum([invoice.fees_earned for invoice in invoices])

    def get_due_date(self, obj):
        invoice_with_earliest_date = obj.invoices.filter(
            payment_status__in=['payment_in_progress', 'payment_failed']
        ).order_by(
            'created'
        ).first()
        return invoice_with_earliest_date.created \
            if invoice_with_earliest_date \
            else None

    def get_amount_paid(self, obj):
        return obj.invoices.filter(
            payment_status='paid'
        ).aggregate(
            Sum('payment__amount')
        )['payment__amount__sum'] or 0

    def get_total_balance(self, obj):
        return obj.invoices.aggregate(
            Sum('payment__amount')
        )['payment__amount__sum'] or 0

    def get_stage(self, obj):
        return obj.stage.title if obj.stage else None

    def get_activity(self, obj):
        activities = \
            models.Activity.objects.filter(
                matter=obj, user=self.context['request'].user
            ).order_by('-created')[:2]
        return ActivityShortSerializer(activities, many=True).data

    class Meta:
        model = models.Matter
        fields = [
            'mediator',
            'title',
            'description',
            'start_date',
            'status',
            'stage',
            'rate',
            'amount_paid',
            'total_balance',
            'due_amount',
            'due_date',
            'shared',
            'activity'
        ]


class UpdateMatterSerializer(MatterSerializer):
    """  Используйте сериализатор для обновлений дела """

    can_change_fields_statuses = [
        models.Matter.STATUS_OPEN, models.Matter.STATUS_CLOSE
    ]

    class Meta(MatterSerializer.Meta):
        # поля, доступные только для чтения, если вопрос является "черновым" или 
        # `ожидающим рассмотрения`
        read_only_fields = MatterSerializer.Meta.read_only_fields + (
            'lead',
            'post',
            'client',
            'mediator',
        )

        # поля, доступные только для чтения, если дело не является "черновым" или 
        # "ожидающим рассмотрения" пользователь может обновлять информацию об основном вопросе 
        # до тех пор, пока она не станет "активной", `завершена" или "отозвана"
        read_only_fields_for_not_draft_or_pending = (
            'city',
            'state',
            'country',
            'rate',
            'rate_type',
            'title',
            'code',
        )

    def get_fields(self):
        """ Сделайте поля доступными только для чтения, за исключением "стадии", для 
        незавершенного дела или его черновика
        Поля, доступные только для чтения, когда дело не находится на рассмотрении или в 
        черновике:
            * city
            * state
            * country
            * rate
            * rate_type
            * title
            * description
            * code
        """
        matter = self.instance
        fields = super().get_fields()

        # Была добавлена проверка "matter is None", потому что, когда swagger генерирует
        # specs -> self.instance отсутствует
        if matter is None or matter.status in self.can_change_fields_statuses:
            return fields

        for field in self.Meta.read_only_fields_for_not_draft_or_pending:
            fields[field].read_only = True

        # сделать поле `design_documents` доступным только для чтения, если текущий 
        # пользователь не первоначальный адвокат по делу
        if self.user and matter.mediator.user != self.user:
            fields['esign_documents'].read_only = True

        return fields

    def validate(self, attrs):
        """
        Не разрешать обновлять поле "design_documents", если "дело" не находится в
        статусах "ожидание" или "черновик".
        """
        self.current_stage = self.instance.stage
        attrs = super().validate(attrs)
        if self.instance is None:
            return attrs

        if (self.instance.status not in self.can_change_fields_statuses
                and attrs.get('esign_documents')):
            raise ValidationError({
                'esign_documents': _(
                    "Esign documents couldn't be uploaded to matter in not "
                    "`pending` or `draft` statuses"
                )
            })
        return attrs

    def update(self, instance, validated_data):
        """ Дополните вопрос документами для электронной подписи """
        esign_documents = validated_data.pop('esign_documents', None)
        instance = super().update(instance, validated_data)
        if self.current_stage != validated_data.get('stage'):
            matter_stage_update.send(
                sender=models.Matter, instance=instance, user=self.user
            )
        if not esign_documents:
            return instance

        adapter = DocuSignAdapter(user=self.user)
        envelope = get_matter_initial_envelope(instance)
        # очистите старый конверт matter из базы данных и аннулируйте его в DocuSign
        adapter.void_envelope(
            envelope=envelope,
            voided_reason='New documents were added to matter'
        )
        # подготовьте новый конверт с документами в DB и DocuSign
        adapter.create_envelope(
            matter=instance,
            documents=[doc['file'] for doc in esign_documents],
            type=Envelope.TYPE_INITIAL
        )
        return instance


class MatterCloseSerializer(serializers.Serializer):
    """Сериализатор, используемый для установки даты "закрыто" при закрытии материала."""
    closed = DateTimeFieldWithTZ(label='Close date of matter')


class ShareMatterSerializer(serializers.Serializer):
    """ Сериализатор, используемый для метода matter API `share`. """
    title = serializers.CharField(required=False, default='', allow_blank=True)
    message = serializers.CharField(required=False, default='', allow_blank=True)  # noqa
    users = serializers.PrimaryKeyRelatedField(
        queryset=AppUser.objects.all().available_for_share(),
        many=True,
        allow_empty=True,
        required=False
    )
    # отдельное поле для "приглашения" новых пользователей
    emails = serializers.ListField(
        child=serializers.EmailField(allow_blank=False, allow_null=False),
        required=False,
        allow_empty=True
    )

    def validate_emails(self, emails: list):
        """ Не позволяет создавать приглашения для уже существующих в базе данных пользователей. """
        if not emails:
            return emails

        existing = [
            email for email in emails if
            AppUser.objects.filter(email__iexact=email).exists()
        ]
        if existing:
            raise ValidationError(
                'Users with these emails already registered in the app: ' +
                ','.join(existing)
            )
        return emails

    def validate(self, attrs):
        """ Игнорируйте поле "электронные письма" для типов пользователей 
        "поддержка" (без приглашений). 
        """
        data = super().validate(attrs)
        return data


class MatterDocumentSerializer(BaseSerializer):
    size = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        #return ''
        return obj.file.split('/')[-1]

    def get_size(self, obj):
        return 100
        #return obj.file.size / 1024

    class Meta:
        model = Document
        fields = (
            'file',
            'name',
            'size',
            'mime_type',
            'created_by',
            'matter',
            'owner'
        )
        read_only_fields = (
            'mime_type',
            'name',
            'size',
        )
