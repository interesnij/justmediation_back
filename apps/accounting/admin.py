from django.contrib import admin
from django.utils.translation import gettext_lazy as _
#from ..core.admin import ReadOnlyAdmin
from . import models


@admin.register(models.QBInvoice)   
class QBInvoiceAdmin(admin.ModelAdmin):
    """Django Admin for QBInvoice model."""
    list_display = (
        'pk', 'user', 'invoice', 'created', 'modified'
    )
    autocomplete_list_filter = (
        'user',
        'invoice',
    )
    list_display_links = ('pk', 'user')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                '_user',
                '_invoice',
                'qb_company_id',
                'qb_invoice_id',
                'qb_customer_id',
                'created',
                'modified',
            )
        }),
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'invoice__title',
        'qb_company_id',
        'qb_invoice_id',
        'qb_customer_id',
    )
    ordering = (
        'pk',
        'created',
        'modified'
    )

    def _user(self, obj):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    def _invoice(self, obj):
        """Return HTML link to `invoice`."""
        return self._admin_url(obj.invoice)
