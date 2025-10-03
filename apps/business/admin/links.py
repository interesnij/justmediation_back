from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin, ReadOnlyAdmin
from .. import models


@admin.register(models.Activity)
class ActivityAdmin(BaseAdmin):
    """ Администратор Django для модели Activity."""
    list_display = (
        'id', 'matter', 'title', 'created', 'modified'
    )
    list_display_links = ('id', 'matter')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'matter',
                'title',
                'user',
            )
        }),
    )
    search_fields = ('title', )
    ordering = ('created',)
    autocomplete_list_filter = (
        'matter',
    )


@admin.register(models.Attachment)
class AttachmentAdmin(BaseAdmin):
    fields = ('file', )


class NoteAttachmentItemInline(admin.TabularInline):
    """Used to show notes attachments"""
    model = models.Note.attachments.through
    verbose_name = _("Attachments")
    verbose_name_plural = _("Attachments")

    def get_queryset(self, request):
        return super().get_queryset(request=request)


@admin.register(models.Note)
class NoteAdmin(BaseAdmin):
    """ Администратор Django для модели Note."""
    list_display = (
        'id', 'matter', 'title', 'created_by', 'created', 'modified'
    )
    list_display_links = ('id', 'matter')
    create_only_fields = (
        'matter',
        'created_by',
    )
    autocomplete_fields = (
        'matter',
        'created_by',
    )
    autocomplete_list_filter = (
        'matter',
        'created_by',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'text',
                'matter',
                'created_by',
            )
        }),
    )
    search_fields = ('title', )
    ordering = ('created',)
    inlines = (
        NoteAttachmentItemInline,
    )


@admin.register(models.VoiceConsent)
class VoiceConsentAdmin(BaseAdmin):
    """ Администратор Django для модели `VoiceConsent`."""
    autocomplete_fields = ('matter',)
    list_display = (
        'id',
        'title',
        'matter',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'file',
                'matter',
            )
        }),
    )
    search_fields = ('title', 'matter__title',)
    ordering = ('created', 'modified')
    create_only_fields = (
        'matter',
    )
    autocomplete_list_filter = (
        'matter',
    )
    list_select_related = (
        'matter',
    )


@admin.register(models.MatterSharedWith)
class MatterSharedWithAdmin(BaseAdmin):
    """ Администратор Django для модели `MatterSharedWith`."""
    autocomplete_fields = ('matter', 'user')
    list_display = (
        'id',
        'matter',
        'user',
    )
    list_display_links = ('id', 'matter', 'user')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'matter',
                'user',
                '_email',
            )
        }),
    )
    search_fields = (
        'matter__title',
        'user__first_name',
        'user__last_name',
    )
    autocomplete_list_filter = (
        'matter',
        'user'
    )
    list_select_related = (
        'matter',
        'user',
    )

    def _email(self, link):
        """Get `email` for shared `link`"""
        if link:
            return link.user.email
        return '-'
