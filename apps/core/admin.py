from typing import Iterable

from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from libs.admin.mixins import (
    BaseObjectActionsMixin,
    FkAdminLink,
    RelatedObjectActionsMixin,
)

from .filters import autocomplete_filter_class


class AutoCompleteFixerMixin:
    """It contains a fix for django-admin-autocomplete-filter.

    Maintainer of package is already working on fix for that.

    """

    autocomplete_list_filter: Iterable[str] = None

    def get_list_filter(self, request):
        """Set up autocomplete filters."""
        list_filter = list(super().get_list_filter(request))
        if not self.autocomplete_list_filter:
            return list_filter
        for autocomplete_filter in self.autocomplete_list_filter:
            list_filter.append(autocomplete_filter_class(autocomplete_filter))
        return list_filter

    class Media:
        pass


class BaseAdmin(
    FkAdminLink,
    AutoCompleteFixerMixin,
    RelatedObjectActionsMixin,
    BaseObjectActionsMixin,
    admin.ModelAdmin
):
    """Base admin representation."""
    save_on_top = True
    list_per_page = 25
    base_change_actions = ['remove']
    # Fields that should be enabled only on creation
    create_only_fields = tuple()

    def get_fieldsets(self, request, obj=None):
        """Add created and modified to fieldsets."""
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets += (
            (_('Extra info'), {
                'fields': [
                    'created',
                    'modified'
                ]
            }),
        )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Add created and modified to readonly_fields.

        Also if create_only_fields were specified add them to readonly_fields,
        if user is working on already created object.

        """
        readonly_fields = super().get_readonly_fields(
            request,
            obj
        )
        readonly_fields = readonly_fields + (
            'created',
            'modified',
        )
        if not self.create_only_fields or not obj:
            return readonly_fields

        return readonly_fields + self.create_only_fields

    def get_change_actions(self, request, object_id, form_url):
        """Add `remove` change action for not production env."""
        actions = super().get_change_actions(request, object_id, form_url)
        if 'remove' in actions and (
            settings.ENVIRONMENT == 'production' or
            not request.user.is_superuser
        ):
            actions.remove('remove')
        if 'remove' not in actions:
            actions.append('remove')
        return actions

    def remove(self, request, obj):
        """Action to `remove` instance.

        It makes instance deletion for all related stuff ignoring PROTECTED
        errors (should be available for not production envs only).

        """
        if obj:
            return obj.remove()

    remove.label = _('Remove')
    remove.short_description = _('Remove instance and its related entities')


class ReadOnlyMixin(AutoCompleteFixerMixin):
    """Forbid editing for admin panel or inline."""

    def has_add_permission(self, request, *args, **kwargs):
        """Disable creation."""
        return False

    def has_change_permission(self, request, obj=None, *args, **kwargs):
        """Disable editing."""
        return False

    def has_delete_permission(self, request, obj=None, *args, **kwargs):
        """Disable deletion."""
        return False


class ReadOnlyAdmin(ReadOnlyMixin, BaseAdmin):
    """Base admin read only representation."""


class ReadOnlyInline(ReadOnlyMixin, admin.TabularInline):
    """Read only inline."""
