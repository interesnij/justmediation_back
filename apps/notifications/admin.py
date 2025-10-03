from django.contrib import admin
from django.core.checks import messages
from django.utils.translation import gettext_lazy as _

from ..core import admin as core_admin
from ..notifications import models
from . import tasks


@admin.register(models.Notification)  
#class NotificationAdmin(core_admin.ReadOnlyAdmin):  
class NotificationAdmin(admin.ModelAdmin):
    """Django Admin for `Notification` model."""
    list_display = ('id', 'title', 'modified')
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'object_id',
                'content_object',
            )
        }),
    )
    search_fields = ('title',)
    ordering = ('modified',)
    related_models = (
        models.NotificationDispatch,
    )


@admin.register(models.NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    """Django Admin for `NotificationType` model."""
    list_display = (
        'id',
        'title',
        'group',
        'runtime_tag',
        'modified',
    )
    list_select_related = (
        'group',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'group',
                'runtime_tag',
                'recipient_type',
                'is_for_mediator',
                'is_for_client',
                'is_for_support',
            )
        }),
    )
    search_fields = (
        'title',
        'runtime_tag'
    )
    list_filter = (
        'group',
        'is_for_mediator',
        'is_for_client',
        'is_for_support',
    )
    readonly_fields = ('runtime_tag', 'group')
    ordering = ('group', 'title')
    related_models = (
        models.Notification,
    )

    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly fields editable on create."""
        if obj:
            return super().get_readonly_fields(request, obj)
        return (
            'runtime_tag',
            'created',
            'modified',
        )


@admin.register(models.NotificationGroup)
class NotificationGroupAdmin(admin.ModelAdmin):
    """Django Admin for `NotificationGroup` model."""
    list_display = ('id', 'title', 'modified')
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
            )
        }),
    )
    search_fields = ('title',)
    ordering = ('title',)
    related_models = (
        models.NotificationType,
    )


@admin.register(models.NotificationSetting)
class NotificationAdmin(admin.ModelAdmin):
#class NotificationSettingAdmin(core_admin.ReadOnlyAdmin):
    """Django Admin for `NotificationSetting` model."""
    list_display = (
        'id',
        'user',
        'by_email',
        'by_push',
        'by_chats',
        'by_matters',
        'by_forums',
        'by_contacts',
    )
    list_display_links = (
        'id',
        'user',
        'by_email',
        'by_push',
        'by_chats',
        'by_matters',
        'by_forums',
        'by_contacts',
    )
    fieldsets = (
        (_('User info'), {
            'fields': (
                'user',
            )
        }),
        (_('Notification info'), {
            'fields': (
                'by_email',
                'by_push',
                'by_chats',
                'by_matters',
                'by_forums',
                'by_contacts',
            )
        })
    )
    list_filter = (
        'user',
    )
    autocomplete_list_filter = (
        'user',
    )
    readonly_fields = ('user',)
    ordering = ('user',)


@admin.register(models.NotificationDispatch)
class NotificationDispatchAdmin(admin.ModelAdmin):
    """Django Admin for `NotificationDispatch` model."""
    list_display = ('id', 'notification', 'recipient', 'status')
    list_display_links = ('id', 'notification', 'status')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'notification',
                'recipient',
                'sender',
                'status',
            )
        }),
    )
    list_filter = (
        'status',
        'notification__type',
        'notification__type__group',
    )
    autocomplete_list_filter = (
        'recipient',
    )
    readonly_fields = (
        'notification',
        'recipient',
        'sender',
        'status',
    )
    ordering = ('modified',)

    actions = (
        'resend_notifications',
    )
    change_actions = [
        'resend_notification',
    ]

    def get_actions(self, request):
        """Restrict admin actions.

        Remove `resend_notifications` for non super users.

        """
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            del actions['resend_notifications']
        return actions

    def get_change_actions(self, request, object_id, form_url):
        """Restrict admin actions.

        Remove `resend_notification` for non super users.

        """
        change_actions = super().get_change_actions(
            request, object_id, form_url
        )
        if not request.user.is_superuser:
            change_actions.remove('resend_notification')
        return change_actions

    def resend_notifications(self, request, queryset):
        """Resend notifications which are not sent."""
        qs = queryset.filter(
            status=models.NotificationDispatch.STATUS_PREPARED
        ).select_related(
            'recipient',
            'notification',
            'notification__type'
        )
        tasks.resend_notifications.delay(qs)
        self.message_user(request, _('Notification resending started'))

    resend_notifications.label = _('Resend notifications')
    resend_notifications.short_description = _('Resend notifications')

    def resend_notification(
        self,
        request,
        notification_dispatch: models.NotificationDispatch
    ):
        """Resend notification if it is not sent."""
        status_prepared = models.NotificationDispatch.STATUS_PREPARED
        if notification_dispatch.status != status_prepared:
            self.message_user(
                request,
                message=_('This notification is already sent'),
                level=messages.ERROR
            )
            return
        tasks.resend_notifications.delay(
            (notification_dispatch,)
        )
        self.message_user(request, _('Notification resend'))

    resend_notification.label = _('Resend notification')
    resend_notification.short_description = _('Resend Notification')
