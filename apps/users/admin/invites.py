from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportMixin
from ...core.admin import BaseAdmin
from .. import models, resources
from .users import SpecialityItemInline


class InviteSpecialityItemInline(SpecialityItemInline):
    """Used to show users specialities from invitation."""
    model = models.Invite.specialities.through


@admin.register(models.Invite)
class InviteAdmin(ImportMixin, BaseAdmin):
    """UI for Invite model."""
    resource_class = resources.InviteResource
    autocomplete_fields = (
        'inviter', 
        'user', 
        #'matter'
    )
    list_display = (
        'uuid',
        'inviter',
        'user',
        #'matter',
        'created',
        'user_type',
        'client_type',
        'type',
        'modified'
    )
    list_display_links = (
        'inviter',
        'user',
    )
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'uuid',
                'inviter',
                'user',
                'user_type',
                'type',
            )
        }),
        (_('User info'), {
            'fields': (
                'email',
                'first_name',
                'last_name',
                'client_type',
                'organization_name',
                '_link_to_user',
                '_link_to_profile',
            )
        }),
        #(_('Extra information from share matter'), {
        #    'fields': (
        #        'title',
        #        'matter'
        #    )
        #}),
        (_('Extra information from WordPress'), {
            'fields': (
                'phone',
                'help_description'
            )
        }),
        (_('Invitation'), {
            'fields': (
                'message',
                'sent'
            )
        }),
    )
    list_filter = (
        'type',
        'user_type',
        'client_type',
    )
    autocomplete_list_filter = (
        'inviter',
        'user',
        #'matter',
    )
    list_select_related = (
        'inviter',
        'user',
        #'matter',
    )
    inlines = (
        InviteSpecialityItemInline,
    )
    readonly_fields = (
        'uuid',
        '_link_to_user',
        '_link_to_profile',
    )
    create_only_fields = (
        'inviter',
    )

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        """Add request's user to resource_kwargs."""
        resource_kwargs = super().get_import_resource_kwargs(
            request, *args, **kwargs
        )
        resource_kwargs['inviter'] = request.user
        return resource_kwargs

    def _link_to_user(self, obj: models.Invite):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to invited user')

    def _link_to_profile(self, obj: models.AppUser):
        """Return HTML link to `profile`."""
        return self._admin_url(getattr(obj.user, obj.user.user_type))

    _link_to_profile.short_description = _('Link to profile of invited user')
