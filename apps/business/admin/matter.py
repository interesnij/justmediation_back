from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin
from ...esign.models import Envelope
from .. import models


@admin.register(models.Lead)
class LeadAdmin(BaseAdmin):
    """ Администратор Django для модели Lead."""
    autocomplete_fields = (
        'mediator',
        'client',
        'post'
    )
    list_display = (
        'id',
        'priority',
        'post',
        'status',
        'created',
        'modified'
    )
    list_display_links = ('id', 'post')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'post',
                'client',
                'mediator',
                'status',
                'priority',
                'chat_channel',
            )
        }),
    )
    search_fields = ('post__title',)
    autocomplete_list_filter = (
        'mediator',
        'client',
        'post',
    )
    list_filter = (
        'priority',
    )
    list_select_related = (
        'post',
        'client',
        'mediator',
    )
    create_only_fields = (
        'post',
        'client',
        'mediator',
        'status'
    )
    readonly_fields = ('chat_channel',)
    ordering = ('created',)
    related_models = (
        models.Matter,
    )


@admin.register(models.Matter)
class MatterAdmin(BaseAdmin):
    """ Администратор Django для модели Matter."""
    list_display = (
        'id',
        'code',
        'title',
        'status',
        'lead',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'code',
        'title',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'code',
                'title',
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'client',
                'mediator',
                'lead',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'stage',
                'completed',
            )
        }),
        (_('Rates'), {
            'fields': (
                'fee_type',
                'rate',
            )
        }),
        (_('Location'), {
            'fields': (
                'country',
                'state',
                'city',
            )
        }),
    )
    search_fields = ('code', 'title',)
    autocomplete_fields = (
        #'country',
        #'state',
        #'city',
        'stage',
        'mediator',
        'client',
        'lead',
    )
    autocomplete_list_filter = (
        'lead',
        'client',
        'mediator',
    )
    list_filter = (
        'status',
    )
    list_select_related = (
        'lead__client',
        'lead__client__user',
        'lead__mediator',
        'lead__mediator__user',
    )
    readonly_fields = ('completed',)
    create_only_fields = (
        'post',
        'client',
        'mediator',
        'status',
        'lead',
    )
    ordering = ('created',)
    related_models = (
        models.BillingItem,
        models.Invoice,
        models.Activity,
        models.Note,
        models.VoiceConsent,
        models.MatterSharedWith,
        Envelope
    )
