from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin
from .. import models


class ContactFormAdmin(admin.ModelAdmin):
    """ Администратор Django для модели ContactForm."""
    list_display = (
        'id',
        'name',
        'email',
        'message',
    )
    list_display_links = (
        'name',
        'email',
        'message',
    )
    search_fields = ('name',)
    ordering = ('created',)

    class Meta:
        model = models.ContactForm

admin.site.register(models.ContactForm, ContactFormAdmin)

class ClientRFPAdmin(admin.ModelAdmin):
    """ Администратор Django для модели ClientRFPAdmin."""
    list_display = (
        'id',
    )
    list_display_links = (
        'id',
    )
    #search_fields = ('mediator_title',)
    ordering = ('id',)

    class Meta:
        model = models.ClientRFP

admin.site.register(models.ClientRFP, ClientRFPAdmin)

class MediatorRFPAdmin(admin.ModelAdmin):
    """ Администратор Django для модели MediatorRFP."""
    list_display = (
        'id',
    )
    list_display_links = (
        'id',
    )
    #search_fields = ('name',)
    ordering = ('id',)

    class Meta:
        model = models.MediatorRFP

admin.site.register(models.MediatorRFP, MediatorRFPAdmin)

@admin.register(models.PostedMatter)
class PostedMatterAdmin(BaseAdmin):
    """ Администратор Django для модели PostedMatter."""
    list_display = (
        'id',
        'title',
        'description',
        'status',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'title',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'client',
                'practice_area',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'status_modified',
            )
        }),
        (_('Budget'), {
            'fields': (
                'budget_min',
                'budget_max',
                'budget_type',
                'budget_detail',
            )
        }),
    )
    search_fields = ('title',)
    autocomplete_fields = (
        'client',
    )
    autocomplete_list_filter = (
        'client',
    )
    list_filter = (
        'status',
    )
    create_only_fields = (
        'budget_min',
        'budget_max',
        'budget_type',
        'budget_detail',
        'status',
    )
    ordering = ('created',)


@admin.register(models.Proposal)
class ProposalAdmin(BaseAdmin):
    """ Администратор Django для модели PostedMatter."""
    list_display = (
        'id',
        'mediator',
        'post',
        'description',
        'status',
        'created',
        'modified'
    )
    list_display_links = (
        'id',
        'description',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'description',
            )
        }),
        (_('Related info'), {
            'fields': (
                'mediator',
                'post',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'status_modified',
            )
        }),
        (_('Rate'), {
            'fields': (
                'rate',
                'rate_type',
                'rate_detail',
                'currency',
            )
        }),
    )
    search_fields = ('title',)
    autocomplete_fields = (
        'mediator',
    )
    autocomplete_list_filter = (
        'mediator',
    )
    list_filter = (
        'status',
    )
    create_only_fields = (
        'status',
    )
    ordering = ('created',)
