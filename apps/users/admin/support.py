from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin
from .. import models

# Usage in change verification statuses in support admin
VERIFICATION_ERROR_MSG = _(
    "You can't change the user status after he started paying or "
    "already paid platform fee."
)


@admin.register(models.Support)
class SupportAdmin(BaseAdmin):
    """Admin for Support model."""
    autocomplete_fields = ('user',)
    list_display = (
        'pk',
        'display_name',
        'email',
        'description',
        'verification_status'
    )
    list_display_links = (
        'pk',
        'display_name',
        'email',
    )
    list_select_related = ('user',)
    autocomplete_list_filter = ('user',)
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'description',
    )
    list_filter = (
        'verification_status',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'user',
                '_link_to_user',
                'email',
                'description',
                'verification_status',
                #'payment_status',
                #'_payment',
            )
        }),
    )
    readonly_fields = (
        'email',
        'display_name',
        'verification_status',
        #'payment_status',
        #'_payment',
        #'_link_to_user',
    )
    create_only_fields = (
        'user',
    )
    #change_actions = [
    #    'verify_support',
    #    'decline_support'
    #]

    #def verify_support(self, request, support: models.Support):
    #    """Verify support profile and send notification email."""
    #    if support.is_in_progress or support.is_paid:
    #        self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
    #        return

    #    support.verify_by_admin()
    #    self.message_user(
    #        request, 'user has been verified', messages.SUCCESS
    #    )

    #verify_support.label = _('Verify')
    #verify_support.short_description = _('Verify profile')

    #def decline_support(self, request, support: models.Support):
    #    """Decline support profile and send notification email."""
    #    if support.is_in_progress or support.is_paid:
    #        self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
    #        return

    #    support.decline_by_admin()
    #    self.message_user(
    #        request, 'user has been declined', messages.SUCCESS
    #    )

    #decline_support.label = _('Decline')
    #decline_support.short_description = _('Decline profile')

    #def _payment(self, obj: models.Support):
    #    """Return HTML link to `payment`."""
    #    return self._admin_url(obj.payment)

    #_payment.short_description = _('Fee payment')

    #def _link_to_user(self, obj: models.Support):
    #    """Return HTML link to `user`."""
    #    return self._admin_url(obj.user)

    #_link_to_user.short_description = _('Link to user')
