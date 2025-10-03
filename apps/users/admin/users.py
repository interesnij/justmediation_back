from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.forms import EmailField
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from apps.users.api.views.utils.verification import resend_email_confirmation
from ...accounting.models import QBInvoice
from ...core.admin import BaseAdmin, ReadOnlyAdmin
from ...esign.models import ESignProfile
from ...finance.models import Payment
from .. import models, resources


class AppUserCreationForm(UserCreationForm):
    """Same as UserCreationForm but without username."""

    class Meta:
        model = models.AppUser
        fields = ('email',)
        field_classes = {'email': EmailField}


class SpecialityItemInline(admin.TabularInline):
    """Used to show inlines specialities"""
    autocomplete_fields = ('speciality',)
    verbose_name = _("User's speciality")
    verbose_name_plural = _("User's specialities")


class AppUserSpecialityItemInline(SpecialityItemInline):
    """Used to show users' specialities."""
    model = models.AppUser.specialities.through


class UserTypeFilter(admin.SimpleListFilter):
    """Used to filter user by their type."""
    title = _('User type')
    parameter_name = 'user_type'

    def lookups(self, request, model_admin):
        """Return filter choices."""
        return (
            ('Is client', _('Is client')),
            ('Is mediator', _('Is mediator')),
        )

    def queryset(self, request, queryset):
        """Filter user by their type.

        Returned queryset depending on input value:
            If value in filter is 'Is client', return clients.
            If value in filter is 'Is mediator', return mediator.
            If value is none of above, return all users.

        """
        lookup_map = {
            'Is client': {'client__isnull': True},
            'Is mediator': {'mediator__isnull': True},
        }
        params = lookup_map.get(self.value())
        if params:
            return queryset.exclude(**params)
        return queryset


@admin.register(models.AppUser)
class AppUserAdmin(ExportMixin, UserAdmin, BaseAdmin):
    """UI for AppUser model."""
    resource_class = resources.AppUserResource
    list_display = (
        'pk',
        'email',
        'first_name',
        'last_name',
        '_user_type_display',
        'is_staff',
    )
    list_display_links = (
        'pk',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {
            'fields': (
                'email',
                'password',
                'is_free_subscription',
            )
        }),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
                'phone',
                '_user_type_display',
                '_link_to_profile',
                'avatar',
                'avatar_display',
                'timezone',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'twofa',
                '_has_active_subscription',
                'groups',
                'user_permissions',
                'onboarding',
            )
        }),
        (_('Important dates'), {
            'fields': (
                'last_login',
                'date_joined'
            )
        }),
    )
    readonly_fields = (
        'avatar_display',
        '_has_active_subscription',
        '_user_type_display',
        '_link_to_profile',
    )
    list_filter = (
        'is_active',
        'is_staff',
        UserTypeFilter,
    )
    list_select_related = (
        'mediator',
        'client',
        'timezone',
    )

    add_form = AppUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
         ),
    )
    inlines = (
        AppUserSpecialityItemInline,
    )
    related_models = (
        models.UserStatistic,
        (Payment, 'payer'),
        ESignProfile,
        QBInvoice,
    )
    change_actions = ['resend_verification']
    ordering = ('email',)

    def avatar_display(self, user):
        """Return html tag with avatar if has one(if not return '-')."""
        if user.avatar:
            return format_html(mark_safe(f'<img src="{user.avatar.url}">'))
        return '-'

    avatar_display.short_description = 'Avatar'

    def _user_type_display(self, obj: models.AppUser):
        """Return user's type."""
        if obj:
            return obj.user_type_display.capitalize()

    _user_type_display.short_description = 'User type'

    def _has_active_subscription(self, obj: models.AppUser):
        """Return `has_active_subscription` of user"""
        return obj.has_active_subscription

    _has_active_subscription.short_description = 'Has active subscription'

    def _link_to_profile(self, obj: models.AppUser):
        """Return HTML link to `profile`."""
        return self._admin_url(getattr(obj, obj.user_type))

    _link_to_profile.short_description = _('Link to profile')

    def resend_verification(self, request, user: models.AppUser):
        """Get mediator's `AccountProxy`."""
        resend_email_confirmation(request, user, True)

    resend_verification.label = _('Resend Verification')
    resend_verification.short_description = _(
        "Resend verification link"
    )


@admin.register(models.UserStatistic)
class UserStatisticAdmin(admin.ModelAdmin):
    """UI for UserStatistic model."""
    autocomplete_fields = ('user',)
    list_display = ('user', 'tag', 'count', 'created')
    list_display_links = ('user', 'tag')
    list_filter = (
        'tag',
    )
    autocomplete_list_filter = (
        'user',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name'
    )
    ordering = (
        'created',
    )
    fieldsets = (
        (_('User info'), {
            'fields': (
                'user',
            )
        }),
        (_('Statistic info'), {
            'fields': (
                'tag',
                'count',
            )
        }),
    )

@admin.register(models.FirmSize)
class FirmSizeAdmin(admin.ModelAdmin):
    """UI for FirmSize model."""
    list_display = ('title',)