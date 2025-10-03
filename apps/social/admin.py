from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from imagekit.admin import AdminThumbnail

from ..chats import tasks as chats_tasks
from ..core.admin import BaseAdmin, ReadOnlyInline
from . import models


class ChatUserInline(ReadOnlyInline):
    """Used to show chats' participants.

    Forbid editing, because m2m_changed isn't triggered when M2M is
    displayed as inline.

    """
    autocomplete_fields = ('appuser',)
    model = models.Chats.participants.through
    verbose_name = _("Chat's participant")
    verbose_name_plural = _("Chat's participants")


@admin.register(models.Chats)
class ChatAdmin(BaseAdmin):
    """Chat representation for admin."""
    list_display = (
        'id',
        'chat_channel',
    )
    list_display_links = ('id', 'chat_channel')
    search_fields = ('chat_channel',)
    readonly_fields = (
        'chat_channel',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'chat_channel',
                'is_group'
            )
        }),
    )
    changelist_actions = (
        'firebase_resync',
    )
    inlines = (
        ChatUserInline,
    )

    def get_changelist_actions(self, request):
        """Restrict admin changelist actions.

        Remove `firebase_resync` for non super users.

        """
        changelist_actions = super().get_changelist_actions(request)
        if not request.user.is_superuser:
            del changelist_actions['firebase_resync']
        return changelist_actions

    def firebase_resync(self, request, queryset):
        """Sync chats in firebase."""
        chats_tasks.firebase_resync.delay()
        self.message_user(request, _('Firebase resync started'))

    firebase_resync.label = _('Firebase Resync')
    firebase_resync.short_description = _('Sync FireBase chats with Backend')


@admin.register(models.MediatorPost)
class MediatorPostAdmin(BaseAdmin):
    """Django Admin for `MediatorPost`."""
    autocomplete_fields = (
        'author',
    )
    autocomplete_list_filter = (
        'author',
    )
    search_fields = ('title',)
    list_display = (
        'id',
        'title',
        'author',
        'created',
        'modified',
    )
    list_display_links = (
        'id',
        'title',
    )
    list_select_related = (
        'author',
        'author__user',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'author',
                'title',
                'image',
                'thumbnail',
                'body',
                'body_preview',
            )
        }),
    )
    thumbnail = AdminThumbnail(image_field='image_thumbnail')
    readonly_fields = (
        'thumbnail',
    )
    create_only_fields = (
        'author',
    )


@admin.register(models.Message)
class MessageAdmin(BaseAdmin):
    """Message representation for admin."""
    list_display = (
        'id',
        'author',
        'chat',
    )
    list_display_links = ('id', 'author', 'chat')
    search_fields = ('author',)
    readonly_fields = (
        'author',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'author',
                'chat',
                'text',
            )
        }),
    )


@admin.register(models.MessageAttachment)
class MessageAttachmentAdmin(BaseAdmin):
    """MessageAttachment representation for admin."""
    list_display = (
        'id',
        'message',
        'file',
        'title',
    )
    list_display_links = ('id', 'message')
    readonly_fields = (
        'message',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'message',
                'file',
                'title',
            )
        }),
    )
