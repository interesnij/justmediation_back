import logging

from libs.docusign.constants import (
    ENVELOPE_STATUS_COMPLETED,
    ENVELOPE_STATUS_CREATED,
)
from libs.docusign.exceptions import NoEnvelopeExistsException

from apps.business.models import Matter

logger = logging.getLogger('django')


def get_matter_initial_envelope(matter: Matter) -> 'Envelope':  # noqa
    """Method to get matter `initial` Envelope."""
    from .models import Envelope
    return matter.envelopes.filter(type=Envelope.TYPE_INITIAL).first()


def get_matter_transition_name_by_envelope(
    matter: Matter, transition_name: str
) -> str:
    """Get corresponding matter transition name by related Envelope.

    Method returns:

        - default `transition_name` if matter has no related envelope
        - `active` if corresponding envelope has a `completed` status
        - `draft` if corresponding envelope has a `created` status
        - `pending` if corresponding envelope has not `completed` and not
        `created` status

        (str) - name of a corresponding to matter transition

    """
    envelope = get_matter_initial_envelope(matter)
    if not envelope:
        return transition_name

    transition_map = {
        ENVELOPE_STATUS_CREATED: 'make_draft',
        ENVELOPE_STATUS_COMPLETED: 'activate',
    }
    return transition_map[envelope.status] \
        if envelope.status in transition_map else 'pending'


def update_matter_status_from_envelope(
    matter: Matter, new_status: str, is_initial: bool
) -> None:
    """Method to update Matter's status from envelope.

    Method allows to update Matter's status from Envelope if:

        - envelope is `initial`
        - matter status was really changed

    """
    if not is_initial:
        return

    # do nothing if matter status is not changed
    if matter.status == new_status:
        return

    # update matter's status through transition
    transition_name = Matter.STATUS_TRANSITION_MAP[new_status]
    getattr(matter, transition_name)()
    matter.save()


def clean_up_removed_in_docusign_envelopes_from_db(envelope):
    """Clean up removed in DocuSign envelopes from DB.

    Attributes:
        envelope (Envelope) - envelope instance which should be checked for
            deletion in DocuSign

    Currently there is a problem in DocuSign that it removes all envelopes for
    `demo` accounts after 30 days and only `draft` envelopes in production
    after 30 days too without any notifications and webhooks.

    https://support.docusign.com/articles/How-long-does-DocuSign-store-my-documents

    Here app handles old envelopes and tries to remove it if possible, there
    are performed following steps:

    1. Try to get `edit` link for envelope:

        - If link could be get - it means that envelope wasn't removed from
        DocuSign yet and we shouldn't clean it up.

        -  If `NoEnvelopeExists` exception is raised - it means that envelope
        was already deleted from DocuSign and we need to clean up it from our
        DB.

        -  If any other exception is raised - it means that we can't get
        `edit` link for this envelope because of absent matter's mediator
        `consent`. So we shouldn't make any envelope deletion here.

    2. Delete envelope and move corresponding matter to `draft` state if its
    `initial` envelope was removed.

    """
    # imported here because of cyclic dependency
    from apps.esign.adapters import DocuSignAdapter

    impersonated_user = envelope.matter.mediator.user
    adapter = DocuSignAdapter(impersonated_user)
    envelope_info = f"Matter ID: {envelope.matter_id}, \n" \
                    f"Envelope ID: {envelope.id} \n"
    try:
        adapter.get_envelope_edit_link(envelope, log_error=False)
        logger.info(
            f"Couldn't delete envelope because it still exists in DocuSign.\n"
            f"{envelope_info}"
        )
        return
    except NoEnvelopeExistsException:
        envelope.delete()
        logger.info(
            f"Deleted not existing envelope.\n{envelope_info}"
            f"Envelope DocuSign ID: {envelope.docusign_id}\n"
        )
    except Exception as e:
        logger.info(
            f"Couldn't delete not existing envelope because of {e}.\n"
            f"{envelope_info}"
        )
        return

    # whenever matter `initial` envelope is deleted -> move matter to `draft`
    # state if it is not `draft`
    if envelope.is_initial and not envelope.matter.is_open:
        envelope.matter.make_draft()
        envelope.matter.save()
