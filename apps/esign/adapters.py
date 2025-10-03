from typing import List

from docusign_esign import Document, EventNotification, Signer

from libs.docusign.clients import DocuSignClient
from libs.docusign.constants import (
    ENVELOPE_STATUS_COMPLETED,
    ENVELOPE_STATUS_DECLINED,
    ENVELOPE_STATUS_DELIVERED,
    ENVELOPE_STATUS_SENT,
    ENVELOPE_STATUS_VOIDED,
)
from libs.docusign.exceptions import UpdateEnvelopeException
from libs.docusign.services import get_envelope_status_notification
from libs.utils import (
    bytes_to_base_64,
    get_file_extension,
    get_filename_from_path,
)

from apps.business.models import Matter
from apps.users.models import AppUser

from . import exceptions, models

__all__ = (
    'DocuSignAdapter',
    'get_envelope_documents',
    'get_envelope_recipients',
    'get_envelope_notification',
)


def get_envelope_documents(envelope: models.Envelope) -> List[Document]:
    """Shortcut to transform Envelope documents in DocuSign format.

    Attributes:
        envelope (Envelope) - envelope which data should be converted

    Returns:
        (list) - envelope documents in accessible by DocuSign format.

    """
    return [
        Document(
            name=doc.name,
            file_extension=get_file_extension(doc.file.url),
            document_base64=bytes_to_base_64(doc.file.read()),
            document_id=idx
        ) for idx, doc in enumerate(envelope.documents.all(), start=1)
    ]


def get_envelope_recipients(envelope: models.Envelope) -> List[Signer]:
    """Shortcut to transform Envelope recipients in DocuSign format.

    Attributes:
        envelope (Envelope) - envelope which data should be converted

    Returns:
        (list) - envelope signers in accessible by DocuSign format.

    """
    recipients = [
        envelope.matter.mediator, envelope.matter.client
    ]
    return [
        Signer(
            email=user.email,
            # docusign doesn't allow to use recipients with names > 100 symbols
            name=user.full_name[:100],
            recipient_id=idx,
            routing_order=idx
        ) for idx, user in enumerate(recipients, start=1)
    ]


def get_envelope_notification(webhook_url: str) -> EventNotification:
    """Shortcut to get event notification.

    Get DocuSign callbacks on Envelope status changes to `sent`, `completed`,
    `declined`, `voided` statuses.

    """
    track_statuses = [
        ENVELOPE_STATUS_SENT,
        ENVELOPE_STATUS_COMPLETED,
        ENVELOPE_STATUS_DECLINED,
        ENVELOPE_STATUS_VOIDED
    ]
    return get_envelope_status_notification(track_statuses, webhook_url)


class DocuSignAdapter:
    """Adapter for current `esign` app integration with DocuSign.

    It defines interactions between app business logic and DocuSign through
    custom methods.

    """

    def __init__(self, user: AppUser) -> None:
        """Initialize DocuSignClient from arguments.

        Attributes:
            user (AppUser) - impersonated user by which DocuSign operations
                are performed

        """
        self.user = user
        self.esign_profile = getattr(user, 'esign_profile', None)
        # initialize original DocuSign client with user
        user_id = self.esign_profile.docusign_id if self.esign_profile else None  # noqa
        self.client = DocuSignClient(user_id=user_id)

    def is_consent_obtained(self) -> bool:
        """Check if consent obtained for impersonated user through DocuSign.

        There is possible case when some mediator had `company` account and
        mediator was fired. In this case the only choice for a company to
        `revoke` app consent for `common` DocuSign user, so all users would
        give consent again. So whenever user `is_consent_obtained` check fails
        - it is needed to remove esign accounts for all `common` DocuSign
        users.

        """
        is_consent_obtained = self.client.is_consent_obtained()
        if is_consent_obtained:
            return is_consent_obtained

        # reset `docusign_id` for current esign profile user
        if self.esign_profile:
            self.esign_profile.docusign_id = None
            self.esign_profile.save()

        # remove all esign profiles for `common` docusign users
        models.ESignProfile.objects.filter(docusign_id=self.client.user_id) \
            .delete()
        return is_consent_obtained

    def get_consent_link(self, return_url: str) -> str:
        """Get `consent` link from DocuSign and create related ESignProfile.

        When consent link is get for a first time for a user there is created a
        new EsignProfile for him with `state` identifier, which allows to match
        returned in DocuSign callback user with original backend one.

        Attributes:
            return_url (str) - url to which user should be redirected after
                obtaining a consent

        """
        # user already has ESignProfile -> remember new url to redirect him
        if self.esign_profile:
            self.esign_profile.return_url = return_url
            self.esign_profile.save()
        # user has no ESignProfile -> create a new one for him
        else:
            self.esign_profile = models.ESignProfile.objects.create(
                user=self.user,
                return_url=return_url
            )
        return self.client.get_consent_link(
            state=self.esign_profile.consent_id
        )

    def save_consent(self, code: str, state: str) -> None:
        """Method to save user data after consent obtaining.

        Attributes:
            code (str) - code returned after following the link from
                `get_consent_link` in browser
            state (str) - state returned after following the link from
                `get_consent_link` in browser to match callback and original
                user in DB

        """
        if not self.esign_profile:
            raise exceptions.SaveUserConsentException

        # check that backend `consent_id` matches `state` from request
        if not state == str(self.esign_profile.consent_id):
            raise exceptions.SaveUserConsentException

        # remember user DocuSign id in ESignProfile to make impersonated
        # requests later
        self.esign_profile.docusign_id = self.client.process_consent(code=code)
        self.esign_profile.save()

    def create_envelope(
        self,
        type: str = None,
        matter: Matter = None,
        documents: List[models.ESignDocument or str] = None,
        envelope: models.Envelope = None,
        is_open: bool = True
    ) -> models.Envelope:
        """Create envelope in DB and DocuSign.

        Method creates new Envelope instance in DocuSign with defined type
        for already existing Envelope or if no `envelope` was set it creates
        new Envelope in DB and then adds it to DocuSign.

        Attributes:
            type (str) - envelope type `initial` or `extra` should be created
            matter (Matter) - matter in which Envelope should be created
            documents (List) - list of documents which should be signed
            envelope (Envelope) - already existing in DB envelope instance
            is_open (bool) - flag if DocuSign Envelope should be draft or not

        Returns:
            (Envelope) - new Envelope instance

        """
        if not envelope:
            envelope = models.Envelope.objects.create(
                matter=matter,
                type=type,
                status=self.client._get_status(is_open)
            )
            models.ESignDocument.objects.bulk_create(
                models.ESignDocument(
                    envelope=envelope,
                    file=doc,
                    order=idx,
                    name=get_filename_from_path(doc)
                ) for idx, doc in enumerate(documents, start=1)
            )

        results = self.client.create_envelope(
            documents=get_envelope_documents(envelope),
            recipients=get_envelope_recipients(envelope),
            is_open=is_open,
            event_notification=get_envelope_notification(
                self.client.envelope_status_webhook_url
            )
        )
        envelope.docusign_id = results.envelope_id
        envelope.status = self.client._get_status(is_open)
        envelope.save()
        # make matter draft again after creating a new `initial` envelope
        if envelope.is_initial:
            envelope.matter.make_draft()
        return envelope

    def void_envelope(
        self, envelope: models.Envelope, voided_reason: str
    ) -> None:
        """Void existing envelope.

        When Envelope is voided it means that it became cancelled and signers
        would get emails that it was voided and what were the reasons of it.

        Attributes:
            envelope (Envelope) - voided Envelope
            voided_reason (str) - reason why Envelope was voided

        """
        if not envelope:
            return

        is_sent = envelope.status in \
            [ENVELOPE_STATUS_SENT, ENVELOPE_STATUS_DELIVERED]
        # only sent or delivered envelopes may be voided
        if is_sent:
            try:
                self.client.update_envelope(
                    envelope_id=envelope.docusign_id,
                    envelope={
                        'status': ENVELOPE_STATUS_VOIDED,
                        'voidedReason': voided_reason
                    }
                )
            # continue work even if envelope could be not updated
            except UpdateEnvelopeException:
                pass
        # after envelope is voided - it may be deleted from DB (cause in this
        # app old envelopes are not stored)
        envelope.delete()

    def get_envelope_edit_link(
        self,
        envelope: models.Envelope,
        return_url: str = '',
        log_error: bool = True,
    ) -> str:
        """Method to get Envelope `edit` view link in DocuSign.

        Attributes:
            envelope (Envelope) - envelope already existing in DB and DocuSign
            return_url (str) - frontend url to which user should be returned
                after working with Envelope editing
            log_error (bool) -
                Should client log error in case of Exception(In some cases when
                caught error is expected, we want to log it as warning instead
                of error, so that sentry won't think of as issue).

        Returns:
            (str) - envelope `edit` view url

        """
        # do nothing if Envelope has no `docusign_id`
        if not envelope or not envelope.docusign_id:
            return ''
        # get edit view link for created Envelope
        return self.client.get_envelope_edit_link(
            envelope_id=envelope.docusign_id,
            return_url=return_url,
            log_error=log_error
        )
