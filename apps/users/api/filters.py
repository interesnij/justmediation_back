from django.db.models import CharField, Count, Q, Value
from django.db.models.functions import Concat

from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404

from django_filters import filters
from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    NumberFilter,
)

from apps.business.models import Matter
from apps.business.models.matter import Lead

from ...users import models
from ..models import AppointmentType, AppUser, Invite, Language

__all__ = (
    'AppUserFilter',
    'MediatorFilter',
    'MediatorUniversityFilter',
    'ClientFilter',
    'SupportFilter'
)


class AppUserFilter(FilterSet):
    """Filter class for `AppUser` model."""
    mediators = BooleanFilter(method='filter_mediators')
    clients = BooleanFilter(method='filter_clients')
    support = BooleanFilter(method='filter_support')
    available_for_share_matter = NumberFilter(
        method='filter_available_for_share_matter'
    )

    class Meta:
        model = models.AppUser
        fields = {
            'id': ['exact', 'in'],
            'email': ['exact', 'in'],
            'specialities': ['exact'],
        }

    def filter_mediators(self, queryset, name, value):
        """Filter mediators users (real users, verified, with subscription).
        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.mediators()
        return queryset

    def filter_clients(self, queryset, name, value):
        """Filter clients users."""
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.clients()
        return queryset

    def filter_support(self, queryset, name, value):
        """Filter support users."""
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.support()
        return queryset

    def filter_available_for_share_matter(self, queryset, name, value):
        """Filter users which are available for sharing matter.

        There available only appusers which haven't been added to matter
        `shared_with` yet.

        """
        user = self.request.user

        if value and user.is_authenticated:
            matter = get_object_or_404(
                Matter.objects.all().available_for_user(user), id=value
            )
            return queryset.available_for_share(matter)
        return queryset


class MediatorFilter(FilterSet):
    """Filter class for `Mediator` model."""
    followed = BooleanFilter(method='filter_followed', )
    has_lead_with_user = BooleanFilter(method='filter_has_lead_with_user', )
    longitude = CharFilter(method='filter_without_filtration')
    latitude = CharFilter(method='filter_without_filtration')
    distance__gte = NumberFilter(field_name='distance', lookup_expr='gte')
    distance__lte = NumberFilter(field_name='distance', lookup_expr='lte')
    appointment_type = filters.ModelMultipleChoiceFilter(
        field_name='appointment_type', queryset=AppointmentType.objects.all()
    )
    spoken_language = filters.ModelMultipleChoiceFilter(
        field_name='spoken_language', queryset=Language.objects.all()
    )

    class Meta:
        model = models.Mediator
        fields = {
            'user': ['exact', 'in'],
            'user__email': ['exact', 'in'],
            'followed': ['exact'],
            'featured': ['exact'],
            'sponsored': ['exact'],
            'user__specialities': ['exact'],
            'fee_types': ['exact'],
            'education__university': ['exact'],
            'practice_jurisdictions': ['exact'],
            'firm_locations__country': ['exact'],
            'firm_locations__city': ['exact'],
            'firm_locations__zip_code': ['exact'],
            'years_of_experience': ['gte'],
            'longitude': ['exact'],
            'latitude': ['exact']
        }

    def filter_followed(self, queryset, name, value):
        """Filter mediators that current user follows.

        If value `true` was passed to filter, we filter queryset to return
        mediators that current user follows.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(followers=user)
        return queryset

    def filter_has_lead_with_user(self, queryset, name, value):
        """Filter mediators that client has dealt with.

        If value `true` was passed to filter and user is client, we filter
        queryset to return mediators that client has a lead with.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.has_lead_with_user(user=user)
        return queryset

    def filter_without_filtration(self, queryset, *args, **kwargs):
        """Filter method, that returns original queryset.

        Dummy filter method to add extra query params to swagger specs that
        are not used in filters, but we need to show them in swagger spec.

        """
        return queryset

class EnterpriseFilter(FilterSet):
    """Filter class for `Enterprise` model."""
    followed = BooleanFilter(method='filter_followed', )
    longitude = CharFilter(method='filter_without_filtration')
    latitude = CharFilter(method='filter_without_filtration')
    distance__gte = NumberFilter(field_name='distance', lookup_expr='gte')
    distance__lte = NumberFilter(field_name='distance', lookup_expr='lte')

    class Meta:
        model = models.Enterprise
        fields = {
            'user': ['exact', 'in'],
            'user__email': ['exact', 'in'],
            'followed': ['exact'],
            'featured': ['exact'],
            'longitude': ['exact'],
            'latitude': ['exact']
        }

    def filter_followed(self, queryset, name, value):
        """Filter enterprise that current user follows.

        If value `true` was passed to filter, we filter queryset to return
        enterprise that current user follows.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.filter(followers=user)
        return queryset

    def filter_without_filtration(self, queryset, *args, **kwargs):
        """Filter method, that returns original queryset.

        Dummy filter method to add extra query params to swagger specs that
        are not used in filters, but we need to show them in swagger spec.

        """
        return queryset


class ClientFilter(FilterSet):
    """Filter class for `Client` model."""

    has_lead_with_user = BooleanFilter(method='filter_has_lead_with_user', )
    has_matter_with_user = BooleanFilter(
        method='filter_has_matter_with_user'
    )
    invited_by_user = BooleanFilter(method='filter_invited_by_user', )
    user_clients = BooleanFilter(method='filter_user_clients', )

    class Meta:
        model = models.Client
        fields = {
            'user': ('exact', 'in'),
            'user__email': ('exact', 'in'),
            'user__specialities': ('exact',),
            'organization_name': ('istartswith', 'icontains'),
            'state': ('exact', 'in'),
            'help_description': ('icontains',),
        }

    def filter_has_lead_with_user(self, queryset, name, value):
        """Filter clients that mediator has dealt with.

        If value `true` was passed to filter and user is mediator, we filter
        queryset to return clients that mediator has a lead with.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.has_lead_with_user(user=user)
        return queryset

    def filter_has_matter_with_user(self, queryset, name, value):
        """Filter clients that mediator has matter with.

        If value `true` was passed to filter and user is mediator, we filter
        queryset to return clients that mediator has a matter with.

        """
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.has_matter_with_user(user=user)
        return queryset

    def filter_invited_by_user(self, queryset, name, value):
        """Filter clients that were invited by user."""
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.invited_by_user(user=user)
        return queryset

    def filter_user_clients(self, queryset, name, value):
        """Filter clients that are clients for user."""
        user = self.request.user

        if value and user.is_authenticated:
            return queryset.user_clients(user=user)
        return queryset


class MediatorUniversityFilter(FilterSet):
    """Filter class for `University` model."""

    class Meta:
        model = models.MediatorUniversity
        fields = {
            'title': ('istartswith', 'icontains'),
        }


class SupportFilter(FilterSet):
    """Filter class for `Support` model."""

    class Meta:
        model = models.Support
        fields = {
            'user': ('exact', 'in'),
            'user__email': ('exact', 'in'),
            'description': ('exact', 'in'),
        }


class IndustryContactsSearchFilter(SearchFilter):
    """Extended search filter to use for method instead of view."""

    def get_search_fields(self, view, request):
        """Returns search fields for industry contacts."""
        return ['first_name', 'last_name']


class IndustryContactsTypeFilter:
    type = CharFilter(method='filter_type')

    def filter_contact_type(self, request, queryset):
        contact_type = request.query_params.get('type')
        if contact_type in ['mediator']:
            if queryset.model == Invite:
                return Invite.objects.none()
            else:
                if contact_type == 'mediator':
                    return queryset.filter(mediator__isnull=False)
        if contact_type == 'pending':
            if queryset.model == Invite:
                return queryset
            else:
                return AppUser.objects.none()
        return queryset


class LeadClientFilter:
    type = CharFilter(method='filter_type')

    def filter_type(self, request, queryset):
        type = request.query_params.get('type')
        if type == 'client':
            if queryset.model == models.Client:
                return queryset.annotate(
                    matter_count=Count('matters')
                ).annotate(
                    lead_count=Count(
                        'leads', filter=Q(leads__status=Lead.STATUS_CONVERTED)
                    )
                ).filter(Q(matter_count__gt=0) | Q(lead_count__gt=0))
            elif queryset.model == Invite:
                return queryset.filter(client_type='client')
        elif type == 'lead':
            if queryset.model == models.Client:
                return queryset.annotate(
                    matter_count=Count('matters')
                ).annotate(
                    lead_count=Count(
                        'leads', filter=Q(leads__status=Lead.STATUS_CONVERTED)
                    )
                ).filter(matter_count=0, lead_count=0)
            elif queryset.model == Invite:
                return queryset.filter(client_type='lead')
        elif type == 'pending':
            if queryset.model == Invite:
                return queryset
            else:
                return AppUser.objects.none()
        elif type == 'not_pending':
            if queryset.model == Invite:
                return AppUser.objects.none()
            else:
                return queryset
        return queryset


class LeadClientSearchFilter(SearchFilter):
    """Extended search filter to use for method instead of view."""

    search = CharFilter(method='search_lead_client')

    def search_lead_client(self, request, queryset):
        search = request.query_params.get('search', '')
        if queryset.model == models.Client:
            return queryset.annotate(
                display_full_name=Concat(
                    'user__first_name', Value(' '),
                    'user__last_name', output_field=CharField()
                )
            ).filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__middle_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(display_full_name__icontains=search)
            )
        elif queryset.model == Invite:
            return queryset.annotate(
                display_full_name=Concat(
                    'first_name', Value(' '),
                    'last_name', output_field=CharField()
                )
            ).filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(middle_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(display_full_name__icontains=search)
            )
        return queryset


class MediatorSearchFilter(SearchFilter):
    """Extended search filter to use for method instead of view."""

    def get_search_fields(self, view, request):
        """Returns search fields for mediator search"""
        return [
            'user__first_name',
            'user__middle_name',
            'user__last_name',
            'user__email'
        ]


class MediatorBillingDetailsSearchFilter(SearchFilter):
    """Extended search filter to use for method instead of view."""

    def get_search_fields(self, view, request):
        """Returns search fields for industry contacts."""
        return [
            'is_billable',
            'billing_type',
            'description',
            'matter__title',
            'matter__code',
            'invoices__title'
        ]


class SpecialityFilter(FilterSet):
    """Filter class for Speciality"""

    class Meta:
        model = models.Speciality
        fields = {
            'title': ['exact', 'in'],
            'created_by': ['exact', 'in', 'isnull'],
        }
