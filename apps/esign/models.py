import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from ..users.models.users import AppUser
from django_fsm import FSMField, transition

from libs.docusign.constants import (
    ENVELOPE_STATUS_COMPLETED,
    ENVELOPE_STATUS_CREATED,
    ENVELOPE_STATUS_DECLINED,
    ENVELOPE_STATUS_DELIVERED,
    ENVELOPE_STATUS_SENT,
    ENVELOPE_STATUS_SIGNED,
    ENVELOPE_STATUS_VOIDED,
)

from apps.business.models import Matter
from apps.core.fields.any_scheme_url import AnySchemeURLModelField
from apps.core.models import BaseModel

from .querysets import EnvelopeQuerySet, ESignProfileQuerySet
from .services import update_matter_status_from_envelope

__all__ = (
    'ESignProfile',
    'Envelope',
    'ESignDocument'
)

def upload_esign_documents_to(instance, filename: str) -> str:
    """Upload instance's `EsignDocuments` to `esign` folder.
    Args:
        instance (Document): instance of document model
        filename (str): file name of document's file
    Returns:
        str: Generated path for ESignDocument's file.
    """
    return 'esign/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )

class ESignProfile(BaseModel):
    """User profile for electronic signification system

    Attributes:
        user (AppUser): participating in electronic signification app user id
        docusign_id (str): id of a user in DocuSign system (GUID) needed for
            impersonalization purpose (send documents from user's face)
        consent_id (str): unique user identifier on backend to match asked for
            consent user with returned from obtaining consent response later
        return_url (str):
            Frontend URL to which user should be returned after consent
            obtaining. The link location, url `scheme` should be added
            manually ("http://" and etc)
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    user = models.OneToOneField(
        AppUser,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='esign_profile'
    )
    docusign_id = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text=_('User GUID in DocuSign')
    )
    consent_id = models.UUIDField(
        default=uuid.uuid4,
        #editable=False,
        unique=True,
        help_text=_(
            'Unique user ID on backend to check consent matching later'
        )
    )
    return_url = AnySchemeURLModelField(
        #editable=False,
        null=True,
        blank=True,
        verbose_name=_('Return url'),
        help_text=_(
            'Frontend URL to which user should be returned after consent '
            'obtaining. The link location, url `scheme` should be added '
            'manually ("http://" and etc)'
        )
    )
    objects = ESignProfileQuerySet.as_manager()

    class Meta:
        verbose_name = _('ESign Profile')
        verbose_name_plural = _('ESign Profiles')

    def __str__(self):
        return f'{self.user}'


class Envelope(BaseModel):
    """Фундаментальный объект, в который упаковываются все необходимые для проектирования операции.

        Конверт содержит документы, связанные материалы и получателей, которые могут быть
        получены из него, другие идентификаторы процесса доставки.

        В качестве конверта могут быть обернуты следующие объекты:

        - bunch of initial matter documents (required for signing documents
        on matter creation without which matter can't be moved to `active`
        status) - `initial` type

        - separate extra document (another document which needed to be signed
        in a matter, but matters status doesn't depend on it) - `extra` type

    There are following possible Envelope statuses:

        - created - envelop is in a draft state and hasn't been sent out for
        signing.

        - sent - email notification with a link to envelope has been sent to
        at least one recipient.

        - delivered - all recipients have viewed the document(s) in an envelope
        through the DocuSign signing web site.

        - signed - the envelope has been signed by all the recipients. This is
        a temporary state during processing, after which the envelope is
        automatically moved to Completed status.

        - completed - the envelope has been completed by all the recipients.

        - declined - the envelope has been declined for signing by one of the
        recipients.

        - voided - the envelope has been voided by the sender.

    Attributes:
        docusign_id (str): id of a user in DocuSign system (GUID) needed for
            impersonalization purpose (send documents from user's face)
        matter (Matter): link to matter in which this envelope is used
        status (str): current envelope status from DocuSign, indicates what is
            a current signing state
        type (str): envelope type `initial` or `extra`
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    docusign_id = models.CharField(
        max_length=40,
        help_text=_('Matter Mediator user GUID in DocuSign'),
        null=True,
        blank=True
    )
    matter = models.ForeignKey(
        'business.Matter',
        on_delete=models.CASCADE,
        related_name='envelopes'
    )

    STATUS_TRANSITION_MAP = {
        ENVELOPE_STATUS_CREATED: 'create',
        ENVELOPE_STATUS_SENT: 'send',
        ENVELOPE_STATUS_DELIVERED: 'deliver',
        ENVELOPE_STATUS_SIGNED: 'sign',
        ENVELOPE_STATUS_COMPLETED: 'complete',
        ENVELOPE_STATUS_DECLINED: 'decline',
        ENVELOPE_STATUS_VOIDED: 'void',
    }
    STATUS_CHOICES = (
        (ENVELOPE_STATUS_CREATED, _('Created')),
        (ENVELOPE_STATUS_SENT, _('Sent')),
        (ENVELOPE_STATUS_DELIVERED, _('Delivered')),
        (ENVELOPE_STATUS_SIGNED, _('Signed')),
        (ENVELOPE_STATUS_COMPLETED, _('Completed')),
        (ENVELOPE_STATUS_DECLINED, _('Declined')),
        (ENVELOPE_STATUS_VOIDED, _('Voided')),
    )
    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=ENVELOPE_STATUS_CREATED,
        help_text=_('Envelope status from DocuSign')
    )

    TYPE_INITIAL = 'initial'
    TYPE_EXTRA = 'extra'

    TYPE_CHOICES = (
        (TYPE_INITIAL, _('Initial')),
        (TYPE_EXTRA, _('Extra'))
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        # None default to force API explicitly set it
        default=None
    )

    objects = EnvelopeQuerySet.as_manager()

    class Meta:
        verbose_name = _('Envelope')
        verbose_name_plural = _('Envelopes')
        constraints = [
            UniqueConstraint(
                fields=['matter'],
                condition=models.Q(type='initial'),
                name='unique_initial_envelope_for_matter'
            )
        ]

    def __str__(self):
        return f'{self.id} for {self.matter} matter'

    @property
    def is_initial(self) -> bool:
        """Designate if Envelope is `initial` or not."""
        return self.type == Envelope.TYPE_INITIAL

    @property
    def is_created(self) -> bool:
        """Designate if Envelope is `created` or not."""
        return self.status == ENVELOPE_STATUS_CREATED

    def clean_type(self):
        """Check that Matter has only one Envelope of `initial` type."""
        if self.type != self.TYPE_INITIAL:
            return

        duplicates = Envelope.objects.filter(
            matter_id=self.matter_id, type=self.TYPE_INITIAL
        ).exclude(id=self.id)
        if duplicates.exists():
            raise ValidationError(_(
                    'Matter should have only one Envelope of `initial` type'
                ))

    @transition(field=status,
                target=ENVELOPE_STATUS_CREATED)
    def create(self):
        """Update envelope status to `created`.

        Whenever Envelope `status` becomes `created`, it is needed to move
        related matter's status to `open` for `initial` envelope.

        """
        update_matter_status_from_envelope(
            matter=self.matter,
            new_status=Matter.STATUS_OPEN,
            is_initial=self.is_initial
        )

    @transition(field=status,
                target=ENVELOPE_STATUS_SENT)
    def send(self):
        """Update envelope status to `sent`.

        Whenever Envelope `status` becomes `sent`, it is needed to move
        related matter's status to `open` for `initial` envelope.

        """
        update_matter_status_from_envelope(
            matter=self.matter,
            new_status=Matter.STATUS_OPEN,
            is_initial=self.is_initial
        )

    @transition(field=status,
                target=ENVELOPE_STATUS_DELIVERED)
    def deliver(self):
        """Update envelope status to `delivered`."""

    @transition(field=status,
                target=ENVELOPE_STATUS_SIGNED)
    def sign(self):
        """Update envelope status to `signed`."""

    @transition(field=status,
                target=ENVELOPE_STATUS_COMPLETED)
    def complete(self):
        """Update envelope status to `completed`.

        Whenever Envelope `status` becomes `completed`, it is needed to move
        related matter's status to `close` for `initial` envelope.

        """
        update_matter_status_from_envelope(
            matter=self.matter,
            new_status=Matter.STATUS_CLOSE,
            is_initial=self.is_initial
        )

    @transition(field=status,
                target=ENVELOPE_STATUS_DECLINED)
    def decline(self):
        """Update envelope status to `declined`.

        Whenever Envelope `status` becomes `declined`, it is needed to move
        related matter's status to `pending` for `initial` envelope.

        """
        update_matter_status_from_envelope(
            matter=self.matter,
            new_status=Matter.STATUS_CLOSE,
            is_initial=self.is_initial
        )

    @transition(field=status,
                target=ENVELOPE_STATUS_VOIDED)
    def void(self):
        """Update envelope status to `voided`.

        Whenever Envelope `status` becomes `voided`, it is needed to move
        related matter's status to `close` for `initial` envelope.

        """
        update_matter_status_from_envelope(
            matter=self.matter,
            new_status=Matter.STATUS_CLOSE,
            is_initial=self.is_initial
        )


class ESignDocument(BaseModel):
    """Separate document for an electronic signification.

    This models stores simple data about file stored in app, which should be
    electronically signed. Like title, link to and etc.

    Attributes:
        envelope (Envelope): link to an envelope in which document should be
            signed
        name (str): document human readable name
        file (str): document's file in storage
        order (int): order of signing for a document within related Envelope
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """
    envelope = models.ForeignKey(
        'Envelope',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    name = models.CharField(
        max_length=255
    )

    file = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(
        #editable=False,
        db_index=True,
        help_text=_('Order of signing for a document within Envelope')
    )

    class Meta:
        verbose_name = _('ESign Document')
        verbose_name_plural = _('ESign Documents')

    def __str__(self):
        return f'{self.name} @ {self.envelope}'
