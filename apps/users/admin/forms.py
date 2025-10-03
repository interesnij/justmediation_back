from django import forms
from django.contrib.admin.widgets import AdminDateWidget, AdminRadioSelect
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import arrow
from apps.finance.constants import PROMO_PERIOD_MONTH
from apps.finance.services.subscriptions import StripeSubscriptionsService
from ..models import Mediator, Enterprise
from ckeditor.widgets import CKEditorWidget


class CancelSubscriptionForm(forms.Form):
    """Custom form to cancel subscription"""

    at_period_end = forms.BooleanField(
        label=_('At period end'),
        help_text=_(
            'By feault subscription will be cancelled immediately'
        ),
        widget=AdminRadioSelect(
            choices=((True, 'Yes'), (False, 'No'))
        ),
        required=True
    )


class VerifyWithTrialForm(forms.Form):
    """Custom form to verify mediator with trial."""
    trial_end = forms.DateField(
        label=_('Trial end'),
        help_text=_(
            f'By default subscription trial is {PROMO_PERIOD_MONTH}-month'
        ),
        widget=AdminDateWidget(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        """Setup dynamic `initial` date and `validators`."""
        super().__init__(*args, **kwargs)
        now = arrow.get(timezone.now())
        self.fields['trial_end'].initial = now.shift(
            months=PROMO_PERIOD_MONTH
        ).date()
        self.fields['trial_end'].validators = [
            MinValueValidator(
                limit_value=now.shift(days=1).date(),
                message=_('Trial end date should be in future')
            ),
            MaxValueValidator(
                limit_value=now.shift(days=730).date(),
                message=_(
                    'The maximum number of trial period days is 730 (2 years).'
                )
            )
        ]


class MediatorForm(
    VerifyWithTrialForm,
    CancelSubscriptionForm,
    forms.ModelForm
):
    """Form for Mediator model."""

    biography = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Mediator
        fields = '__all__'

    #def __init__(self, *args, **kwargs):
        """Set up separate `trial_end` field absent in Mediator model.

        There is a following business logic:

            1. The field is disabled when:

              - Mediator is not verified
              - Mediator has no active subscription yet
              - Mediator has active subscription, which is not `trialing`
              - form is used for new Mediator creation

            2. The field is editable in all other cases.

        """
    #    super().__init__(*args, **kwargs)
        # make keywords field not required
    #    self.fields['keywords'].required = False

    #    self.fields['trial_end'].required = False
    #    self.fields['trial_end'].initial = None
    #    self.fields['trial_end'].widget.attrs['disabled'] = True

        # if new Mediator is created from forms
    #    if not self.instance or self.instance._state.adding:
    #        return

        # set up initial `trial_end` when user has subscription
    #    subscription = self.instance.user.active_subscription
    #    if subscription and self.instance.is_verified:
    #        self.fields['trial_end'].initial = subscription.trial_end

        # enable field if he has `trialing` subscription
    #    if subscription and subscription.is_trialing:
    #        self.fields['trial_end'].widget.attrs['disabled'] = False

    #def save(self, **kwargs):
    #    """Overridden `save` to process  `trial_end` update if needed."""
    #    trial_end = self.cleaned_data.pop('trial_end', None)
    #    obj = super().save(**kwargs)
    #    subscription = obj.user.active_subscription
        # if `trial_end` was updated
    #    if trial_end and subscription:
    #        is_trial_end_changed = subscription.trial_end.date() != trial_end
    #        if is_trial_end_changed:
    #            subscription.update(
    #                trial_end=StripeSubscriptionsService.date_to_timestamp(
    #                    trial_end
    #                )
    #            )
    #    return obj

class EnterpriseForm(VerifyWithTrialForm, forms.ModelForm):
    """Form for Enterprise model."""

    class Meta:
        model = Enterprise
        fields = '__all__'
