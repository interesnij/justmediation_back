from django.core.exceptions import ValidationError
from rest_framework import serializers
from apps.core.api.serializers import BaseSerializer
from apps.forums.api.serializers import PracticeAreaSerializer
from apps.forums.models import ForumPracticeAreas
from apps.users.api.serializers import (
    AppUserWithoutTypeSerializer,
    MediatorOverviewSerializer,
    ClientInfoSerializer,
    CurrenciesSerializer,
)
from ...models import PostedMatter, Proposal


class ProposalShortSerializer(BaseSerializer):
    """ Систематизирует предложения адвокатов по опубликованным вопросам """
    name = serializers.CharField(
        source='mediator.user.full_name',
        read_only=True
    )
    mediator_data = AppUserWithoutTypeSerializer(
        source='mediator.user',
        read_only=True
    )
    currency_data = CurrenciesSerializer(
        source='currency',
        read_only=True
    )

    class Meta:
        model = Proposal
        fields = (
            'id',
            'name',
            'created',
            'rate',
            'rate_type',
            'description',
            'mediator_data',
            'status',
            'status_modified',
            'currency',
            'currency_data',
            'is_hidden_for_client',
            'is_hidden_for_mediator',
        )


class ProposalSerializer(BaseSerializer):
    """ Систематизирует предложения адвокатов по опубликованным вопросам """
    name = serializers.CharField(
        source='mediator.user.full_name',
        read_only=True
    )
    post = serializers.PrimaryKeyRelatedField(
        queryset=PostedMatter.objects.all(),
        write_only=True
    )
    mediator_data = MediatorOverviewSerializer(
        source='mediator', read_only=True
    )
    currency_data = CurrenciesSerializer(
        source='currency',
        read_only=True
    )

    def validate(self, attrs):
        if not hasattr(self.user, 'mediator'):
            raise ValidationError('Only mediators can submit proposal')
        if attrs['post'].status == PostedMatter.STATUS_INACTIVE:
            raise ValidationError('Engagement is inactive')
        attrs['mediator'] = self.user.mediator
        return super().validate(attrs)

    class Meta:
        model = Proposal
        fields = (
            'id',
            'name',
            'created',
            'rate',
            'description',
            'rate_type',
            'rate_detail',
            'post',
            'mediator',
            'mediator_data',
            'status',
            'status_modified',
            'post_id',
            'currency',
            'currency_data',
            'is_hidden_for_client',
            'is_hidden_for_mediator',
        )
        read_only_fields = (
            'id',
            'name',
            'created',
            'status',
            'post_id'
        )
        extra_kwargs = {
            'mediator': {
                'required': False
            },
            'rate_detail': {
                'required': False
            },
            'currency': {
                'required': False
            },
        }


class PostedMatterSerializer(BaseSerializer):
    """ Сериализует дела, размещенные клиентом. """
    budget_min = serializers.CharField(required=False, allow_blank=True)
    proposals = serializers.SerializerMethodField(read_only=True)
    practice_area_data = PracticeAreaSerializer(
        source='practice_area', read_only=True
    )
    client_data = ClientInfoSerializer(source='client', read_only=True)
    currency_data = CurrenciesSerializer(source='currency', read_only=True)

    def get_proposals(self, obj):
        """
        Возвращает только предложения адвоката, если пользователь прошел проверку подлинности
        есть ли еще какие-либо предложения по опубликованному вопросу
        """
        proposals = []
        if self.context.get('request'):
            mediator = getattr(
                self.context.get('request').user,
                'mediator',
                None
            )
            if mediator:
                for proposal in obj.proposals.all():
                    if proposal.mediator == mediator and \
                            proposal.status != 'withdrawn':
                        proposals.append(proposal)
        if not proposals:
            for proposal in obj.proposals.all():
                if proposal.status != 'withdrawn':
                    proposals.append(proposal)
        return ProposalShortSerializer(proposals, many=True).data

    def validate(self, attrs):
        if not hasattr(self.user, 'client'):
            raise ValidationError('Can not post matter')
        attrs['client'] = self.user.client
        return super().validate(attrs)

    class Meta:
        model = PostedMatter
        fields = (
            'id',
            'title',
            'description',
            'budget_min',
            'budget_max',
            'budget_type',
            'budget_detail',
            'practice_area',
            'created',
            'proposals',
            'client',
            'client_data',
            'practice_area_data',
            'currency',
            'currency_data',
            'status',
            'status_modified',
            'is_hidden_for_client',
            'is_hidden_for_mediator',
        )
        read_only_fields = (
            'status',
            'status_modified',
            'currency_data'
        )
        extra_kwargs = {
            'client': {
                'required': False
            },
            'budget_detail': {
                'required': False
            }
        }


class PostedMatterShortSerializer(BaseSerializer):
    """ Сериализует материалы, размещенные клиентом. """

    client_data = ClientInfoSerializer(source='client', read_only=True)
    practice_area_data = PracticeAreaSerializer(
        source='practice_area',
        read_only=True
    )

    class Meta:
        model = PostedMatter
        fields = (
            'id',
            'title',
            'description',
            'budget_min',
            'budget_max',
            'budget_type',
            'budget_detail',
            'practice_area',
            'practice_area_data',
            'created',
            'client',
            'client_data',
            'status',
            'is_hidden_for_client',
            'is_hidden_for_mediator',
        )


class PostedMattersByPracticeAreaSerializer(BaseSerializer):
    """ Упорядочивает размещенные дела по областям практики. """
    posted_matters_count = serializers.SerializerMethodField(read_only=True)
    posted_matters = serializers.SerializerMethodField(read_only=True)
    last_posted = serializers.SerializerMethodField(read_only=True)
    latest_posted_matter_created = serializers.SerializerMethodField(
        read_only=True
    )

    def get_latest_posted_matter_created(self, obj):
        if obj.posted_matter.count():
            return obj.posted_matter.all()[0].created

    def get_posted_matters(self, obj):
        return PostedMatterSerializer(
            obj.posted_matter.all(),
            read_only=True,
            many=True,
            context=self.context
        ).data

    def get_posted_matters_count(self, obj):
        return obj.posted_matter.count()

    def get_last_posted(self, obj):
        objs = obj.posted_matter.all()
        if len(objs) > 0:
            return objs[0].created
        else:
            return None

    class Meta:
        model = ForumPracticeAreas
        fields = (
            'id',
            'title',
            'description',
            'last_posted',
            'posted_matters_count',
            'posted_matters',
            'created',
            'latest_posted_matter_created'
        )
        read_only_fields = (
            'created',
        )


class MediatorProposalSerializer(BaseSerializer):
    """ Упорядочивает предложения адвокатов """
    post_data = PostedMatterShortSerializer(source='post', read_only=True)
    currency = CurrenciesSerializer(
        source='mediator.fee_currency',
        read_only=True
    )

    class Meta:
        model = Proposal
        fields = (
            'id',
            'rate',
            'rate_type',
            'description',
            'created',
            'post_data',
            'currency',
            'status',
            'status_modified',
            'is_hidden_for_client',
            'is_hidden_for_mediator',
        )
