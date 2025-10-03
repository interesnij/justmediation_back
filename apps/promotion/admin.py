from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..core.admin import BaseAdmin
from . import models


@admin.register(models.Event)
class EventAdmin(BaseAdmin):
    """Event representation for admin."""
    list_display = (
        'id',
        'title',
        'mediator',
        'timezone',
        'is_all_day',
        'start',
        'end',
    )
    autocomplete_fields = ('mediator', )
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    readonly_fields = (
        'duration',
    )
    create_only_fields = (
        'mediator',
        'timezone',
    )
    list_filter = (
        'is_all_day',
    )
    autocomplete_list_filter = (
        'mediator',
    )
    list_select_related = (
        'mediator',
        'mediator__user',
    )
    ordering = ('start', 'end')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'description',
                'mediator',
                'timezone',
            )
        }),
        (_('Time'), {
            'fields': (
                'start',
                'end',
                'duration',
                'is_all_day',
            )
        }),
        (_('Location'), {
            'fields': (
                'location',
            )
        }),
    )
