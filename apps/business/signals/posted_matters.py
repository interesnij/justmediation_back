from django.db.models import signals
from django.dispatch import Signal, receiver

from apps.business.models import Proposal

new_proposal = Signal(providing_args=('instance',))
new_proposal.__doc__ = (
    'Signal that indicates that mediator has submitted a proposal.'
)

proposal_withdrawn = Signal(providing_args=('instance',))
proposal_withdrawn.__doc__ = (
    'Signal that indicates that mediator has submitted a proposal.'
)

proposal_accepted = Signal(providing_args=('instance',))
proposal_accepted.__doc__ = (
    'Signal that indicates that mediator has submitted a proposal.'
)

post_inactivated = Signal(providing_args=('instance',))
post_inactivated.__doc__ = (
    'Signal that indicates that client has inactivated his posted matter.'
)

post_reactivated = Signal(providing_args=('instance',))
post_reactivated.__doc__ = (
    'Signal that indicates that client has reactivated his posted matter.'
)


@receiver(signals.post_save, sender=Proposal)
def new_proposal_submitted(instance: Proposal, created: bool, **kwargs):
    """Send signal that indicates that mediator has submitted a proposal."""
    if not created:
        return

    new_proposal.send(sender=Proposal, instance=instance)
