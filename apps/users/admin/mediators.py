from django.contrib import admin, messages
from django.contrib.gis.admin import OSMGeoAdmin
from django.shortcuts import redirect, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from libs.utils import json_prettified
from ...business import models as business_models
from ...core.admin import BaseAdmin
from ...promotion import models as promotion_models
from ...social import models as social_models
from .. import models
from .forms import MediatorForm, CancelSubscriptionForm, VerifyWithTrialForm



@admin.register(models.MediatorEducation)
class MediatorEducationAdmin(admin.ModelAdmin):
    list_display = ['id',]
    class Meta:
            model = models.MediatorEducation

class PracticeJurisdictionItemInline(admin.TabularInline):
    """Used to show mediator practice jurisdictions."""
    autocomplete_fields = ('jurisdiction',)
    model = models.Mediator.practice_jurisdictions.through
    verbose_name = _("Mediator's practice jurisdiction")
    verbose_name_plural = _("Mediator's practice jurisdictions")


class FirmLocationItemInline(admin.TabularInline):
    """Used to show mediator firm locations."""
    autocomplete_fields = ('firmlocation',)
    model = models.Mediator.firm_locations.through
    verbose_name = _("Mediator's firm locations")
    verbose_name_plural = _("Mediator's firm locations")


class FeeKindItemInline(admin.TabularInline):
    """Used to show mediator fee kinds."""
    autocomplete_fields = ('feekind',)
    model = models.Mediator.fee_types.through
    verbose_name = _("Mediator's fee kind")
    verbose_name_plural = _("Mediator's fee kinds")


class MediatorEducationItemInline(admin.TabularInline):
    """Used to show mediator education"""
    autocomplete_fields = ('university',)
    model = models.MediatorEducation
    verbose_name = _("Mediator's education")
    verbose_name_plural = _("Mediator's education")


class MediatorRegistrationAttachmentItemInline(admin.TabularInline):
    """Used to show mediator attachments on registration"""
    model = models.MediatorRegistrationAttachment
    verbose_name = _("Mediator's attachments")
    verbose_name_plural = _("mediator's attachments")

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related(
            'mediator',
            'mediator__user',
        )


# Usage in change statuses in mediator admin
VERIFICATION_ERROR_MSG = _(
    "You can’t change the mediator's status after creating a subscription."
)


class MediatorVerificationMixin:
    """Mixin to provide mediator verification functionality."""
    change_actions = [
        'verify_mediator',
        'decline_mediator',
        'cancel_subscription'
    ]

    def verify_mediator(self, request, mediator: models.Mediator):
        """Verify mediator profile and send notification email."""
        if mediator.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
        
        return self.verify_mediator_view(request, mediator)

    verify_mediator.label = _('Verify')
    verify_mediator.short_description = _('Verify mediator profile')

    def decline_mediator(self, request, mediator: models.Mediator):
        """Decline mediator profile and send notification email."""
        if mediator.user.has_active_subscription:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
        
        mediator.decline_by_admin()

    decline_mediator.label = _('Decline')
    decline_mediator.short_description = _(
        'Decline mediator profile verification'
    )

    def cancel_subscription(self, request, mediator: models.Mediator):
        """Cancel mediator subscription"""
        if not mediator.user.customer:
            self.message_user(request, VERIFICATION_ERROR_MSG, messages.ERROR)
            return
        return self.cancel_subscription_view(request, mediator)

    cancel_subscription.label = _('Cancel Subscription')
    cancel_subscription.short_description = _(
        "Cancel active subscription of attonrey"
    )

    def verify_mediator_view(self, request, mediator: models.Mediator):
        """ Отдельное представление для обеспечения проверки адвокатом.
        Это представление позволяет администратору выбрать пробный период для еще не 
        верифицированного пользователя.
        """

        form = VerifyWithTrialForm(request.POST or None)

        # if form is valid -> perform mediator verification
        if request.method == 'POST' and form.is_valid():
            mediator.verify_by_admin(
                trial_end=form.cleaned_data['trial_end']
            )
            return redirect(reverse(
                'admin:users_mediator_change',
                kwargs={'object_id': mediator.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Verify mediator profile')
        context['form'] = form 
        context['opts'] = self.model._meta
        context['object'] = mediator
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )

    def cancel_subscription_view(self, request, mediator: models.Mediator):
        """Separate view to cancel mediator subscription.

        This view allows admin to cancel mediator subscription
        immediately or not.

        """

        form = CancelSubscriptionForm(request.POST or None)

        # if form is valid -> perform mediator verification
        if request.method == 'POST' and form.is_valid():
            from apps.finance.services import stripe_subscriptions_service
            at_period_end = form.cleaned_data['at_period_end']
            if mediator.user.customer:
                stripe_subscriptions_service(mediator.user).\
                    cancel_current_subscription(at_period_end)
            return redirect(reverse(
                'admin:users_mediator_change',
                kwargs={'object_id': mediator.pk}
            ))

        context = self.admin_site.each_context(request)
        context['title'] = _('Cancel mediator subscription')
        context['form'] = form
        context['opts'] = self.model._meta
        context['object'] = mediator
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request,
            'users/verify_with_trial.html',
            context
        )


from django import forms
class Mediator2AdminForm(forms.ModelForm):
    from ckeditor.widgets import CKEditorWidget

    biography = forms.CharField(widget=CKEditorWidget(), required = False)
    class Meta:
        model = models.Mediator
        fields = '__all__'

class MediatorAdmin2(admin.ModelAdmin):
    """Admin UI for FollowedTopic admin."""

    search_fields = ['user__last_name']
    form = Mediator2AdminForm
    

#admin.site.register(models.Mediator, MediatorAdmin)

@admin.register(models.Mediator)
class MediatorAdmin(
    MediatorVerificationMixin,
    OSMGeoAdmin,
    BaseAdmin
):
    """Mediator representation for admin."""
    form = MediatorForm
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
        'email',
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
    )
    list_filter = (
        'featured',
        'sponsored',
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
                #'_link_to_user',
                #'email',
                'verification_status',
                #'followers_count',
                'featured',
                'biography',
                'firm_name',
            )
        }),
        (_('Sponsor info'), {
            'fields': (
                'sponsored',
                'sponsor_link',
            )
        }),
        (_('Finance info'), {
            'fields': (
                #'_subscription',
                #'_subscription_status',
                #'_is_paid',
                #'_canceled_at',
                'trial_end',
            )
        }),
        (_('Practice information'), {
            'fields': (
                'license_info',
                'practice_description',
                'years_of_experience',
            )
        }),
        (_('Speciality'), {
            'fields': (
                'have_speciality',
                'speciality_time',
                #'speciality_matters_count',
            )
        }),
        (_('Fees'), {
            'fields': (
                'fee_rate',
                'tax_rate',
            )
        }),
        (_('Extra info'), {
            'fields': (
                'extra_info',
                'charity_organizations',
                'keywords',
            )
        }),
    )
    #readonly_fields = (
    #    'verification_status',
    #    'email',
    #    'followers_count',
    #    '_is_paid',
    #    '_subscription',
    #    '_subscription_status',
    #    '_canceled_at',
    #    '_link_to_user',
    #)
    create_only_fields = (
        'user',
    )
    inlines = (
        MediatorRegistrationAttachmentItemInline,
        PracticeJurisdictionItemInline,
        FirmLocationItemInline,
        MediatorEducationItemInline,
        FeeKindItemInline,
    )
    #related_models = (
    #    (business_models.Matter, 'mediator'),
    #    business_models.Lead,
    #    business_models.Stage,
    #    business_models.ChecklistEntry,
    #    promotion_models.Event,
    #    social_models.MediatorPost,
    #)
    #change_actions = MediatorVerificationMixin.change_actions + \
    #    ['get_account_proxy']

    def _link_to_user(self, obj: models.Mediator):
        """Return HTML link to `user`."""
        return self._admin_url(obj.user)

    _link_to_user.short_description = _('Link to user')

    def _subscription(self, mediator):
        """Return info about current mediator subscription."""
        subscription = mediator.user.active_subscription
        return self._admin_url(subscription) if subscription else '-'

    _subscription.short_description = _('Subscription')

    def _subscription_status(self, mediator):
        """Return info about current mediator subscription status."""
        subscription = mediator.user.active_subscription
        return subscription.status.capitalize() if subscription else '-'

    _subscription_status.short_description = _('Subscription status')

    def _is_paid(self, mediator):
        """Return info about current mediator subscription payment."""
        subscription = mediator.user.active_subscription
        is_paid = subscription.is_active if subscription else False

        return 'Yes' if is_paid else 'No'

    _is_paid.short_description = _('Is subscription paid')

    def _canceled_at(self, mediator):
        """Return info about current mediator subscription cancel."""
        subscription = mediator.user.active_subscription
        return subscription.canceled_at.date() \
            if subscription.canceled_at else '-'

    _canceled_at.short_description = _('Canceled at')

    def _firm_place_id(self, mediator):
        """Return a link to google maps, which shows location."""
        if not mediator.firm_place_id:
            return None
        place_id = mediator.firm_place_id
        url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
        link = format_html(
            "<a href='{0}'>Open in google maps</a>", url, place_id
        )
        return link

    _firm_place_id.short_description = _('Link to place')

    def _firm_location(self, mediator):
        """Return a link to google maps, which shows location of mediator."""
        if not mediator.firm_location:
            return None
        lon, lat = mediator.firm_location
        url = f'http://maps.google.com/maps?t=h&q=loc:{lat},{lon}'
        link = format_html("<a href='{0}'>{1}, {2}</a>", url, lat, lon)
        return link

    _firm_location.short_description = _('Coordinates (latitude, longitude)')

    def firm_location_data_prettified(self, mediator):
        """Prettify location data."""
        return json_prettified(mediator.firm_location_data)

    def followers_count(self, mediator):
        """Return followers count."""
        return mediator.followers.count()

    followers_count.short_description = _('Followers count')

    def get_account_proxy(self, request, mediator: models.Mediator):
        """Get mediator's `AccountProxy`."""
        deposit_account = mediator.user.deposit_account
        if not deposit_account:
            msg = 'mediator has no direct deposit account yet'
            self.message_user(request, msg, messages.ERROR)
            return
        return redirect(self._get_admin_url(deposit_account))

    get_account_proxy.label = _('Account Proxy')
    get_account_proxy.short_description = _(
        "mediator's direct deposit account"
    )
