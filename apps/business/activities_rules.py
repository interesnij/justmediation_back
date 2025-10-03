"""File with related to matter Activities Rules.

Rules define cases when activity should be generated and for what signals. Each
rule behaves as a signal to `create_activity` for some conditions.

"""

from functools import partial

from django.db.models import signals

from django_fsm.signals import post_transition

from apps.documents.models import Document

from . import models
from .services.activities import checks
from .services.activities.rules import ActivityRule, create_activity
from .signals import invoice_is_sent


class MatterStatusActivityRule(ActivityRule):
    """Custom rule for Matter status changed `activity`."""
    status_msg_map = {
        models.Matter.STATUS_OPEN:
            'Matter agreement opened signature by {client}',
        models.Matter.STATUS_REFERRAL: 'Matter referral to {user}',
        models.Matter.STATUS_CLOSE: 'Matter closed by {user}',
    }

    def get_activity_msg(self, instance: models.Matter, **kwargs) -> str:
        """Overridden method to add custom activity message."""
        msg_template = self.msg_template or self.status_msg_map[instance.status]  # noqa
        if '{client}' in msg_template:
            user = instance.client.user
            attr = 'client'
        else:
            method_kwargs = kwargs.get('method_kwargs')
            user = method_kwargs and method_kwargs.get('user') or \
                instance.mediator.user
            attr = 'user'
        return msg_template.format(**{attr: user.display_name})


ACTIVITIES_SIGNALS = (
    ActivityRule(
        sender=signals.post_save,
        model=models.Matter,
        checks=(checks.is_created,),
        msg_template='Matter created by {user}',
        related_user_lookup='mediator.user',
    ),
    MatterStatusActivityRule(
        sender=post_transition,
        checks=(checks.is_not_open,),
        model=models.Matter,
        related_user_lookup='mediator.user'
    ),
    ActivityRule(
        sender=invoice_is_sent,
        model=models.Invoice,
        msg_template='Invoice was sent to client by {user}',
        related_user_lookup='created_by',
        matter_lookup='matter',
        type=models.Activity.ACTIVITY_TYPE_INVOICE
    ),
    ActivityRule(
        sender=signals.post_save,
        model=models.BillingItem,
        msg_template='Billing Item was added by {user}',
        related_user_lookup='created_by',
        matter_lookup='matter',
        type=models.Activity.ACTIVITY_TYPE_BILLING_ITEM
    ),
    ActivityRule(
        sender=signals.post_save,
        checks=(checks.is_created,),
        model=models.Note,
        msg_template='Note has been added by {user}',
        related_user_lookup='created_by',
        matter_lookup='matter',
        type=models.Activity.ACTIVITY_TYPE_NOTE
    ),
    ActivityRule(
        sender=signals.post_save,
        checks=(checks.is_created,),
        model=models.MatterComment,
        msg_template='Message has been added by {user}',
        related_user_lookup='author',
        matter_lookup='matter',
        type=models.Activity.ACTIVITY_TYPE_MESSAGE
    ),
    ActivityRule(
        sender=signals.post_save,
        checks=(checks.is_created, checks.is_shared_folder_document),
        model=Document,
        msg_template='New file has been uploaded to shared folder by {user}',
        related_user_lookup='created_by',
        matter_lookup='matter',
        type=models.Activity.ACTIVITY_TYPE_DOCUMENT
    ),
    ActivityRule(
        sender=signals.post_save,
        checks=(checks.is_created,),
        model=models.VoiceConsent,
        msg_template='Voice consent has been uploaded by {user}',
        related_user_lookup='matter.client.user',
        matter_lookup='matter',
    ),
)


# connect activities signals from rules
for rule in ACTIVITIES_SIGNALS:
    rule.sender.connect(
        receiver=partial(create_activity, rule=rule),
        sender=rule.model,
        weak=False
    )
