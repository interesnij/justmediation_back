from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ...business import models as business_models
from ...core.admin import BaseAdmin
from .. import models


@admin.register(models.Client)
class ClientAdmin(BaseAdmin):
    """UI for Client model."""
    autocomplete_fields = (
        'user',
        #'state',
    )
    list_display = (
        'pk',
        'display_name',
        'email',
        'client_type',
        'state',
    )
    list_display_links = (
        'pk',
        'display_name',
        'email',
    )
    list_filter = (
        'client_type',
    )
    list_select_related = (
        'country',
        'state',
        'city',
        'user',
    )
    autocomplete_list_filter = (
        'user',
        'state',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'organization_name',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'user',
                '_link_to_user',
                'email'
            )
        }),
        (_('Client info'), {
            'fields': (
                'client_type',
                'organization_name',
                'country',
                'state',
                'city',
                'help_description',
            )
        }),
    )
    readonly_fields = (
        'email',
        'display_name',
        '_link_to_user',
    )
    create_only_fields = (
        'user',
    )
    #related_models = (
    #    business_models.Matter,
    #    business_models.Lead,
    #)

    def _link_to_user(self, obj: models.Mediator):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to user')
