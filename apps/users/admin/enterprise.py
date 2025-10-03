from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.shortcuts import redirect, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from libs.utils import json_prettified
from ...core.admin import BaseAdmin
from .. import models
from .forms import EnterpriseForm


class EnterpriseMemberAdmin(BaseAdmin):
    list_display = ('email',)
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'email',
            )
        }),
    )
@admin.register(models.Member)
class EnterpriseMember2Admin(EnterpriseMemberAdmin):
    """Admin panel for speciality"""

class EnterpriseMembers2Admin(BaseAdmin):
    list_display = ('enterprise', 'user', 'invitee', 'type', 'state')
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'enterprise',
                'invitee',
                'user',
                'type',
                'state',
            )
        }),
    )
@admin.register(models.EnterpriseMembers)
class EnterpriseMembersAdmin(EnterpriseMembers2Admin):
    """Admin panel for speciality"""

class FirmLocationItemInline(admin.TabularInline):
    """Used to show enterprise firm locations."""
    autocomplete_fields = ('firmlocation',)
    model = models.Enterprise.firm_locations.through
    verbose_name = _("Enterprise's firm locations")
    verbose_name_plural = _("Enterprise's firm locations")


class TeamMemberInvitedItemInline(admin.TabularInline):
    """Used to show enterprise team members"""
    # autocomplete_fields = ('invitee', 'user',)
    model = models.Enterprise.team_members_invited.through
    verbose_name = _("Enterprise's team member")
    verbose_name_plural = _("Enterprise's team members")


# Usage in change statuses in enterprise admin
VERIFICATION_ERROR_MSG = _(
    "You can’t change the enterprise's status after creating a subscription."
)


class EnterpriseVerificationMixin:
    """Mixin to provide Enterprise verification functionality."""
    change_actions = [
        'verify_enterprise',
        'decline_enterprise'
    ]

    def verify_enterprise(self, request, enterprise: models.Enterprise):
        """Verify enterprise profile and send notification email."""
        return self.verify_enteprise_view(request, enterprise)

    verify_enterprise.label = _('Verify')
    verify_enterprise.short_description = _('Verify enterprise profile')

    def decline_enterprise(self, request, enterprise: models.Enterprise):
        """Decline enterprise profile and send notification email."""
        enterprise.decline_by_admin()

    decline_enterprise.label = _('Decline')
    decline_enterprise.short_description = _(
        'Decline enterprise profile verification'
    )

    def verify_enteprise_view(self, request, enterprise: models.Enterprise):
        """Separate view to provide enterprise verification.

        This view allows admin to select trial period for a not verified yet
        user.

        """

        if request.method == 'POST':
            enterprise.verify_by_admin()
            return redirect(reverse(
                'admin:users_enterprise_change',
                kwargs={'object_id': enterprise.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Verify enterprise profile')
        context['opts'] = self.model._meta
        context['object'] = enterprise
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )


@admin.register(models.Enterprise)
class EnterpriseAdmin(
    EnterpriseVerificationMixin,
    OSMGeoAdmin,
    BaseAdmin
):
    """Mediator representation for admin."""
    form = EnterpriseForm
    autocomplete_fields = (
        'user',
    )
    list_display = (
        'pk',
        'user',
        'email',
        'verification_status'
    )
    list_display_links = (
        'pk',
        'user',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    list_filter = (
        'featured',
        'verification_status',
    )
    autocomplete_list_filter = (
        'user',
    )
    ordering = (
        '-pk',
        'user',
        'verification_status'
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'user',
                'email',
                '_link_to_user',
                'team_logo',
                'verification_status',
                'followers_count',
                'featured',
            )
        }),
        (_('Location info'), {
            'fields': (
                'firm_name',
                'firm_size',
                'firm_locations',
            )
        }),
    )
    readonly_fields = (
        'verification_status',
        'email',
        'followers_count',
        '_link_to_user',
    )
    create_only_fields = (
        'user',
    )
    inlines = (
        FirmLocationItemInline,
        TeamMemberInvitedItemInline,
    )
    change_actions = EnterpriseVerificationMixin.change_actions + \
        ['get_account_proxy']

    def _link_to_user(self, obj: models.Enterprise):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to user')

    def _firm_place_id(self, enterprise):
        """Return a link to google maps, which shows location."""
        if not enterprise.firm_place_id:
            return None
        place_id = enterprise.firm_place_id
        url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        link = format_html(
            "<a href='{0}'>Open in google maps</a>", url, place_id
        )
        return link

    _firm_place_id.short_description = _('Link to place')

    def _firm_location(self, enterprise):
        """Return a link to google maps, which shows location of enterprise."""
        if not enterprise.firm_location:
            return None
        lon, lat = enterprise.firm_location
        url = f'http://maps.google.com/maps?t=h&q=loc:{lat},{lon}'
        link = format_html("<a href='{0}'>{1}, {2}</a>", url, lat, lon)
        return link

    _firm_location.short_description = _('Coordinates (latitude, longitude)')

    def firm_location_data_prettified(self, enterprise):
        """Prettify location data."""
        return json_prettified(enterprise.firm_location_data)

    def followers_count(self, enterprise):
        """Return followers count."""
        return enterprise.followers.count()

    followers_count.short_description = _('Followers count')

    def get_account_proxy(self, request, enterprise: models.Enterprise):
        """Get enterprise's `AccountProxy`."""
        deposit_account = enterprise.user.deposit_account
        if not deposit_account:
            msg = 'Enteprise has no direct deposit account yet'
            self.message_user(request, msg, messages.ERROR)
            return
        return redirect(self._get_admin_url(deposit_account))

    get_account_proxy.label = _('Account Proxy')
    get_account_proxy.short_description = _(
        "Enterprise's direct deposit account"
    )
