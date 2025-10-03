from django_filters import rest_framework as filters
from django_filters.rest_framework import NumberFilter
from django_filters.widgets import RangeWidget
from .. import models


class LeadFilter(filters.FilterSet):
    """ Отфильтруйте по вложенным полям для модели лидирования. """

    class Meta:
        model = models.Lead
        fields = {
            'id': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'mediator': ['exact', 'in'],
            'client': ['exact', 'in'],
            'status': ['exact', 'in'],
        }


class OpportunityFilter(filters.FilterSet):
    """ Фильтровать по вложенным полям для модели Opportunity."""

    class Meta:
        model = models.Opportunity
        fields = {
            'id': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'mediator': ['exact', 'in'],
            'client': ['exact', 'in'],
        }


class MatterFilter(filters.FilterSet):
    """ Фильтровать по вложенным полям для модели Matter."""
    shared_with = NumberFilter(
        method='filter_shared_with'
    )

    class Meta:
        model = models.Matter
        fields = {
            'id': ['exact', 'in'],
            'lead': ['exact', 'in'],
            'mediator': ['exact', 'in'],
            'client': ['exact', 'in'],
            'country': ['exact', 'in'],
            'city': ['exact', 'in'],
            'state': ['exact', 'in'],
            'status': ['exact', 'in'],
            'stage': ['exact', 'in'],
            'speciality': ['exact', 'in'],
            'invite': ['exact', 'in'],
        }

    def filter_shared_with(self, queryset, name, value):
        """ Фильтруйте материал, которым делятся со мной """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(shared_with__in=[value])


class BillingItemFilter(filters.FilterSet):
    """ Фильтровать по вложенным полям для модели BillingItem. """
    invoice = filters.NumberFilter(method='filter_by_invoice')

    class Meta:
        model = models.BillingItem
        fields = {
            'id': ['exact', 'in'],
            'matter': ['exact', 'in'],
            'billing_type': ['exact', 'in'],
            'is_billable': ['exact', 'in'],
            'date': ['gte', 'lte'],
            'created': ['gte', 'lte'],
        }

    def filter_by_invoice(self, queryset, name, value):
        """ Отфильтруйте время выставления счетов для счета-фактуры. """
        if value:
            return queryset.filter(attached_invoice__invoice=value)
        return queryset


class InvoiceFilter(filters.FilterSet):
    """ Фильтровать по вложенным полям для модели Invoice. """

    class PeriodRangeWidget(RangeWidget):
        """ Чтобы настроить суффиксы для фильтра `период`. """
        suffixes = ['start', 'end']

    period = filters.DateFromToRangeFilter(
        widget=PeriodRangeWidget,
        method='filter_period',
        help_text=(
            "This is not the filter field you're looking for, "
            'use `period_start` and `period_end`'
        )
    )
    # Фильтр "Дата от до диапазона" ищет `period_start` и `period_end`
    # мы добавляем эти два для спецификации swagger
    period_start = filters.CharFilter(
        method='filter_without_filtration',
        help_text='Example: `2020-01-10`'
    )
    period_end = filters.CharFilter(
        method='filter_without_filtration',
        help_text='Example: `2020-01-10`'
    )

    matter__client__first_name__istartswith = filters.CharFilter(
        lookup_expr='istartswith',
        field_name='matter__client__user__first_name'
    )
    matter__client__first_name__icontains = filters.CharFilter(
        lookup_expr='icontains',
        field_name='matter__client__user__first_name'
    )
    matter__client__last_name__istartswith = filters.CharFilter(
        lookup_expr='istartswith',
        field_name='matter__client__user__last_name'
    )
    matter__client__last_name__icontains = filters.CharFilter(
        lookup_expr='icontains',
        field_name='matter__client__user__last_name'
    )

    class Meta:
        model = models.Invoice
        fields = {
            'id': ['exact', 'in'],
            'created_by': ['exact', 'in'],
            'client': ['exact', 'in'],
            'matter': ['exact', 'in'],
            'matter__mediator': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'title': ['istartswith', 'icontains'],
            'matter__client__organization_name': ['istartswith', 'icontains'],
            'status': ['exact', 'in'],
            'payment_status': ['exact', 'in'],
            'period_start': [
                'year__gte',
                'year__lte',
                'month__gte',
                'month__lte',
            ],
            'period_end': [
                'year__gte',
                'year__lte',
                'month__gte',
                'month__lte',
            ],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }

    def filter_period(self, queryset, name, value: slice):
        """ Отфильтруйте счета-фактуры, которые относятся к входному периоду времени. """
        if value and value.start and value.stop:
            period_start = value.start
            period_end = value.stop
            return queryset.match_period(
                period_start=period_start,
                period_end=period_end
            )
        return queryset

    def filter_without_filtration(self, queryset, *args, **kwargs):
        """Метод фильтрации, который возвращает исходный набор запросов.
        Метод фиктивного фильтра для добавления дополнительных параметров запроса к 
        спецификациям swagger, которые не используются в фильтрах, но нам нужно показать 
        их в спецификации swagger.
        """
        return queryset


class ActivityFilter(filters.FilterSet):
    """ Фильтр для модели `Activity`. """

    class Meta:
        model = models.Activity
        fields = {
            'id': ['exact', 'in'],
            'user': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'type': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class NoteFilter(filters.FilterSet):
    """ Фильтр для модели `Note` """

    class Meta:
        model = models.Note
        fields = {
            'id': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__mediator': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'created_by': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class MatterPostFilter(filters.FilterSet):
    """ Фильтр для модели `MatterPost`. """

    class Meta:
        model = models.MatterPost
        fields = {
            'id': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'matter': ['exact', 'in'],
            'matter__mediator': ['exact', 'in'],
            'matter__client': ['exact', 'in'],
            'seen': ['exact', 'in'],
            'seen_by_client': ['exact', 'in'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class MatterCommentFilter(filters.FilterSet):
    """ Фильтр для модели `MatterComment`. """

    class Meta:
        model = models.MatterComment
        fields = {
            'post': ['exact', 'in'],
            'text': ['icontains', 'istartswith'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class VoiceConsentFilter(filters.FilterSet):
    """ Фильтр для модели `VoiceConsent`. """

    class Meta:
        model = models.VoiceConsent
        fields = {
            'matter': ['exact', 'in'],
            'title': ['icontains', 'istartswith'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class VideoCallFilter(filters.FilterSet):
    """ Фильтр для модели `VideoCall`. """

    class Meta:
        model = models.VideoCall
        fields = {
            'id': ['exact', 'in'],
            'participants': ['exact'],
            'created': ['gte', 'lte'],
            'modified': ['gte', 'lte'],
        }


class ChecklistEntryFilter(filters.FilterSet):
    """ Фильтр для модели `ChecklistEntry` (just for swagger spec)."""
    matter = filters.NumberFilter(method='noop_filter')

    class Meta:
        model = models.ChecklistEntry
        fields = {
            'id': ['exact', 'in'],
        }

    def noop_filter(self, queryset, name, value):
        """ Отсутствие фильтрации (реализовано на уровне просмотра) """
        return queryset


class StageFilter(ChecklistEntryFilter):
    """ Фильтр для модели `Stage` (just for swagger spec)."""

    class Meta:
        model = models.Stage
        fields = {
            'id': ['exact', 'in'],
            'mediator': ['exact', 'in']
        }


class MatterSharedWithFilter(filters.FilterSet):
    """ Фильтр для модели  `MatterSharedWith`. """

    class Meta:
        model = models.MatterSharedWith
        fields = {
            'id': ['exact', 'in'],
            'user': ['exact', 'in'],
            'matter': ['exact', 'in'],
        }


class PostedMatterFilter(filters.FilterSet):
    """ Фильтр для модели `PostedMatter`. """

    class Meta:
        model = models.PostedMatter
        fields = {
            'id': ['exact', 'in'],
            'client': ['exact', 'in'],
            'status': ['exact', 'in'],
            'is_hidden_for_client': ['exact', 'in'],
            'is_hidden_for_mediator': ['exact', 'in'],
        }


class ProposalFilter(filters.FilterSet):
    """ Фильтр для модели `Proposal`. """

    class Meta:
        model = models.Proposal
        fields = {
            'id': ['exact', 'in'],
            'mediator': ['exact', 'in'],
            'post': ['exact', 'in'],
            'status': ['exact', 'in'],
            'is_hidden_for_client': ['exact', 'in'],
            'is_hidden_for_mediator': ['exact', 'in'],
        }
