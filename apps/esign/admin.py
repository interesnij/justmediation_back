from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from ..core.admin import ReadOnlyAdmin
from . import models
from .adapters import DocuSignAdapter


class BaseESignAdmin(admin.ModelAdmin):
    """Base ESign Admin with common behaviors.

    Not allow admin users to create, update or delete related to electronic
    signing instances, they can just list and retrieve existing data. All
    entities creation would be made on backend side.

    """
    pass


@admin.register(models.ESignProfile)
class ESignProfileAdmin(BaseESignAdmin):
    """Django Admin for ESignProfile model."""
    list_display = (
        'pk', 'user', 'docusign_id', 'consent_id', 'created', 'modified'
    )
    list_display_links = ('pk', 'docusign_id')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                '_user',
                'docusign_id',
                'consent_id',
                'return_url',
            )
        }),
    )
    search_fields = ('docusign_id', 'consent_id', 'user__email')
    ordering = ('created',)
    readonly_fields = ('consent_id', 'return_url')
    autocomplete_list_filter = (
        'user',
    )

    def _user(self, obj):
        """Return html tag with user if has one(if not return '-')."""
        return self._admin_url(obj.user)


@admin.register(models.Envelope)
class EnvelopeAdmin(BaseESignAdmin):
    """Django Admin for Envelope model."""
    list_display = (
        'id', 'docusign_id', 'matter', 'status', 'type', 'created', 'modified'
    )
    list_display_links = ('id', 'docusign_id')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                '_matter',
                'docusign_id',
                'status',
                'type',
            )
        }),
    )
    search_fields = ('docusign_id', 'matter__title', 'matter__code')
    ordering = ('created',)
    related_models = (
        models.ESignDocument,
    )
    list_filter = (
        'status',
        'type'
    )
    autocomplete_list_filter = (
        'matter',
    )
    change_actions = [
        'get_envelope_edit_link',
    ]

    def get_envelope_edit_link(self, request, obj):
        """Action to get Envelope edit link."""
        if obj:
            try:
                provider = DocuSignAdapter(user=request.user)
                url = provider.get_envelope_edit_link(envelope=obj)
                self.message_user(request, message=f'Edit link: {url}')
            except Exception as e:
                self.message_user(request, e.message, messages.ERROR)

    get_envelope_edit_link.label = _('Get Envelope edit link')

    def _matter(self, obj):
        """Return html tag with matter if has one(if not return '-')."""
        return self._admin_url(obj.matter)


@admin.register(models.ESignDocument)
class ESignDocumentAdmin(BaseESignAdmin):
    """Django Admin for ESignDocument model."""
    list_display = (
        'id', 'envelope', 'name', 'order', 'created', 'modified'
    )
    list_display_links = ('id', 'name')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                '_envelope',
                'name',
                'file',
                'order',
            )
        }),
    )
    search_fields = ('name',)
    ordering = ('created',)
    readonly_fields = ('order',)
    autocomplete_list_filter = (
        'envelope',
    )

    def _envelope(self, obj):
        """Return html tag with envelope if has one(if not return '-')."""
        return self._admin_url(obj.envelope)
