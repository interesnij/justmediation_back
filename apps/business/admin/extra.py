from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin, ReadOnlyAdmin
from .. import models


@admin.register(models.Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ['id',]
    class Meta:
            model = models.Opportunity


@admin.register(models.Stage)
class StageAdmin(BaseAdmin):
    """ Администратор Django для модели `Stage`. """
    list_display = (
        'id',
        'title',
        'mediator',
    )
    list_display_links = ('id', 'title')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'mediator',
                'title',
            )
        }),
    )
    search_fields = ('title',)
    create_only_fields = (
        'mediator',
    )
    autocomplete_fields = (
        'mediator',
    )
    autocomplete_list_filter = (
        'mediator',
    )
    ordering = ('created', 'modified')
    related_models = (
        models.Matter,
    )


@admin.register(models.ChecklistEntry)
class ChecklistEntryAdmin(BaseAdmin):
    """ Администратор Django для модели `Запись контрольного списка`. """
    list_display = (
        'id',
        'mediator',
        'description',
    )
    list_display_links = ('id', 'mediator')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'mediator',
                'description',
            )
        }),
    )
    search_fields = ('description',)
    create_only_fields = ('mediator',)
    autocomplete_fields = ('mediator',)
    autocomplete_list_filter = (
        'mediator',
    )
    ordering = ('created', 'modified')


@admin.register(models.Referral) 
class ReferralAdmin(BaseAdmin):
    """ Администратор Django для модели  `Referral`."""
    list_display = (
        'id',
        'mediator',
        'message'
    )
    list_display_links = ('id', 'message')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'mediator',
                'message',
            )
        }),
    )
    search_fields = ('message',)
    create_only_fields = (
        'mediator',
    )
    autocomplete_fields = (
        'mediator',
    )
    autocomplete_list_filter = (
        'mediator',
    )
    related_models = (
        models.Matter,
    )


@admin.register(models.PaymentMethods)
class PaymentMethodsAdmin(BaseAdmin):
    """ Администратор Django для модели `PaymentMethods`."""
    list_display = (
        'id',
        'title',
    )
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
