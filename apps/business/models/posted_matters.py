from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from apps.core.models import BaseModel
from apps.forums.models import ForumPracticeAreas
from apps.users.models.extra import Currencies
from ...users.models.users import AppUser
from ...users.models.mediators import Mediator
from ...users.models.clients import Client
from ...users.models.extra import *


class ContactForm(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_('First name')
    )
    email = models.EmailField(
        verbose_name=_('Email'),
        null=True,
    )
    message = models.CharField(
        max_length=1000,
        verbose_name=_('Message')
    )
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_INACTIVE, _('Inactive'))
    )
    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status')
    )
    status_modified = models.DateTimeField(
        default=timezone.now,
        help_text=_('Datetime when status was modified'),
        verbose_name=_('Status Modified')
    )

    class Meta:
        verbose_name="Message from contact form"
        verbose_name_plural="Messages from contact form"


class ClientRFP(BaseModel):
    open_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Open submission'),)
    close_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Close submission'),)
    dedline_open_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Dedline Open submission'),)
    dedline_close_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Dedline Open submission'),)
    individ_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Individ date'),)
    documents = models.TextField(null=True, blank=True, verbose_name=_('Documents'))
    description = models.CharField(null=True, blank=True, max_length=1000, verbose_name=_('Description'))
    potencial_client_conflicts = models.CharField(null=True, blank=True, max_length=1000, verbose_name=_('Potencial Client Conflicts'))
    company_or_duns = models.CharField(null=True, blank=True, max_length=500, verbose_name=_('Company or DUNS'))
    who_can_respond_to_rfp = models.CharField(null=True, blank=True, max_length=500, verbose_name=_('Who Can Respond To RFP'))
    responsible_mediator_qualifications = models.CharField(null=True, blank=True, max_length=1000, verbose_name=_('Responsible mediator Qualifications'))
    location_license_admissions = models.CharField(null=True, blank=True, max_length=500, verbose_name=_('Location license admissions'))
    anticipated_period = models.CharField(null=True, blank=True, max_length=50, verbose_name=_('Anticipated period'))
    range_of_packages = models.CharField(null=True, blank=True, max_length=50, verbose_name=_('Range of packages'))
    expected_extention = models.CharField(null=True, blank=True, max_length=50, verbose_name=_('Expected extention'))
    mediators_count = models.CharField(null=True, blank=True, max_length=50, verbose_name=_('Number of mediators Needed'))
    inquiries_user = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.CASCADE,verbose_name=_('Inquiries user'),related_name='inquiries_user')
    dedlain_user = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.CASCADE,verbose_name=_('Dedlain user'),related_name='dedlain_user')
    mediators = models.ManyToManyField(AppUser, verbose_name=_('mediator Credentials for Aforementioned requirements'),related_name='client_rfp_mediators')
    specialities = models.ManyToManyField(Speciality, verbose_name=_('Practice Area where help needed'),related_name='rfp_client_specialities')
    scope_of_services = models.ManyToManyField(Speciality, verbose_name=_('SCOPE OF SERVICES'),related_name='client_scope_of_services')
    mediators_specialities = models.ManyToManyField(Speciality, verbose_name=_('mediators need to be Qualified in Legal Practice'),related_name='client_mediators_specialities')
    license_admissions = models.ManyToManyField(Speciality, verbose_name=_('License Requirements & BAR Admissions'),related_name='client_license_admissions')

    hourly_fee_enabled = models.BooleanField(default=False, verbose_name=_('hourly fee enabled'),)
    success_fee_enabled = models.BooleanField(default=False, verbose_name=_('success fee enabled'),)
    sliding_scale_fee_enabled = models.BooleanField(default=False, verbose_name=_('sliding scale fee enabled'),)
    litigation_funding_enabled = models.BooleanField(default=False, verbose_name=_('litigation funding enabled'),)
    retainer_fee_enabled = models.BooleanField(default=False, verbose_name=_('retainer fee enabled'),)
    subscription_fee_enabled = models.BooleanField(default=False, verbose_name=_('subscription fee enabled'),)
    bended_rate_enabled = models.BooleanField(default=False, verbose_name=_('bended rate enabled'),)
    hybrid_fee_enabled = models.BooleanField(default=False, verbose_name=_('hybrid fee enabled'),)
    contingency_fee_enabled = models.BooleanField(default=False, verbose_name=_('contingency fee enabled'),)
    caped_fee_enabled = models.BooleanField(default=False, verbose_name=_('caped fee enabled'),)
    proect_bases_fee_enabled = models.BooleanField(default=False, verbose_name=_('proect bases fee enabled'),)

    class Meta:
        verbose_name="Client RFP"
        verbose_name_plural="Client RFP"

class MediatorRFP(BaseModel):
    open_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Open submission'),)
    close_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Close submission'),)
    dedline_open_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Dedline Open submission'),)
    dedline_close_submission = models.DateTimeField(null=True, blank=True, verbose_name=_('Dedline Open submission'),)
    documents = models.TextField(null=True, blank=True, verbose_name=_('Documents'))
    description = models.CharField(null=True, blank=True, max_length=1000, verbose_name=_('Description'))
    inquiries_user = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.CASCADE,verbose_name=_('Inquiries user'),related_name='mediator_inquiries_user')
    dedlain_user = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.CASCADE,verbose_name=_('Dedlain user'),related_name='mediator_dedlain_user')
    mediators = models.ManyToManyField(AppUser,verbose_name=_('mediator Credentials for Aforementioned requirements'),related_name='mediator_rfp_mediators')
    respond_mediators = models.ManyToManyField(AppUser, verbose_name=_('mediator Qualities for Aforementioned requirements'),related_name='respond_mediator_rfp_mediators')
    specialities = models.ManyToManyField(Speciality, null=True, blank=True, verbose_name=_('Practice Area where help needed'),related_name='mediator_client_specialities')
    scope_of_services = models.ManyToManyField(Speciality, null=True, blank=True, verbose_name=_('SCOPE OF SERVICES'),related_name='mediator_scope_of_services')
    mediators_count = models.CharField(null=True, blank=True, max_length=50, verbose_name=_('Number of mediators Needed'))
    location = models.CharField(null=True, blank=True, max_length=500, verbose_name=_('Location'))
    location_license_admissions = models.CharField(null=True, blank=True, max_length=500, verbose_name=_('Location license admissions'))
    no_conflict = models.BooleanField(default=False, verbose_name=_('no conflict?'),)
    review_draft_negatiate = models.BooleanField(default=False, verbose_name=_('review draft negatiate?'),)
    advise_individual_labor = models.BooleanField(default=False, verbose_name=_('advise individual labor?'),)
    advise_individual = models.BooleanField(default=False, verbose_name=_('advise individual?'),)
    mediator_can_accept_responsibility = models.BooleanField(default=False, verbose_name=_('mediator can accept responsibility?'),)
    anticipated_contract_period_enabled = models.BooleanField(default=False, verbose_name=_('anticipated contract period enabled?'),)
    fee_structure_enabled = models.BooleanField(default=False, verbose_name=_('fee structure enabled?'),)

    class Meta:
        verbose_name="mediator RFP"
        verbose_name_plural="mediator RFP"

class PostedMatter(BaseModel):
    """
    Атрибуты: 
        client (CLient): Клиент, создавший сообщение о проблеме
        title (str): название вопроса
        description (текст): простое описание вопроса простыми словами
        budget (плавающий): сумма клиентского бюджета
        budget_type (str): может быть почасовым
            flat_fee
            непредвиденные обстоятельства
            other_fee
        currency (str): валюта клиента
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_('Client'),
        related_name='posted_matters'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title')
    )
    practice_area = models.ForeignKey(
        ForumPracticeAreas,
        verbose_name=_('Related practice area'),
        on_delete=models.PROTECT,
        related_name='posted_matter',
        null=True,
        blank=True,
    )
    BUDGET_TYPE_HOURLY = 'hourly'
    BUDGET_TYPE_FLAT = 'flat_fee'
    BUDGET_TYPE_CONTINGENCY_FEE = 'contingency_fee'
    BUDGET_TYPE_OTHER = 'other'

    BUDGET_TYPE_CHOICES = (
        (BUDGET_TYPE_HOURLY, _('Hourly')),
        (BUDGET_TYPE_FLAT, _('Flat Fee')),
        (BUDGET_TYPE_CONTINGENCY_FEE, _('Contingency Fee')),
        (BUDGET_TYPE_OTHER, _('Other Fee'))
    )
    budget_min = models.CharField(
        max_length=50,
        verbose_name=_('Budget Min'),
    )
    budget_max = models.CharField(
        max_length=50,
        verbose_name=_('Budget Max'),
    )
    budget_type = models.CharField(
        max_length=25,
        verbose_name=_('Budget type'),
        choices=BUDGET_TYPE_CHOICES,
        default=BUDGET_TYPE_HOURLY,
    )
    budget_detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Budget description'),
        help_text=_('Budget description')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Extra matter description')
    )
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, _('Active')),
        (STATUS_INACTIVE, _('Inactive'))
    )
    status = FSMField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name=_('Status')
    )
    status_modified = models.DateTimeField(
        default=timezone.now,
        help_text=_('Datetime when status was modified'),
        verbose_name=_('Status Modified')
    )
    currency = models.ForeignKey(
        Currencies,
        on_delete=models.PROTECT,
        default=1,
        verbose_name=_('Currency'),
        related_name='posted_matters'
    )
    is_hidden_for_client = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for client')
    )
    is_hidden_for_mediator = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for mediator')
    )

    @transition(
        field=status,
        source=STATUS_ACTIVE,
        target=STATUS_INACTIVE
    )
    def deactivate(self):
        self.status_modified = timezone.now()
        self.proposals.update(status=Proposal.STATUS_CLOSED_BY_CLIENT)

    @transition(
        field=status,
        source=STATUS_INACTIVE,
        target=STATUS_ACTIVE
    )
    def reactivate(self):
        self.status_modified = timezone.now()
        self.proposals.update(status=Proposal.STATUS_PENDING)


class Proposal(BaseModel):
    """
    Содержит подробную информацию о предложениях адвокатов.
    Атрибуты:
        mediator (mediator): ссылка на адвоката, подающего предложение
        rate (decimal): Ставка, предложенная адвокатом
        description (text): Детали предложения, представленные адвокатом
        post (Опубликованный материал): Ссылка на опубликованный материал
        status (str): статус предложения может находиться
            pending
            accepted
            revoked
            chat
    """
    mediator = models.ForeignKey(
        Mediator,
        on_delete=models.PROTECT,
        verbose_name=_('Mediator'),
        related_name='proposals'
    )
    rate = models.CharField(
        max_length=50,
        verbose_name=_('rate'),
    )
    RATE_TYPE_HOURLY = 'hourly'
    RATE_TYPE_FLAT = 'flat_fee'
    RATE_TYPE_CONTINGENCY_FEE = 'contingency_fee'
    RATE_TYPE_OTHER = 'other'

    RATE_TYPE_CHOICES = (
        (RATE_TYPE_HOURLY, _('Hourly')),
        (RATE_TYPE_FLAT, _('Flat Fee')),
        (RATE_TYPE_CONTINGENCY_FEE, _('Contingency Fee')),
        (RATE_TYPE_OTHER, _('Other Fee'))
    )
    rate_type = models.CharField(
        max_length=25,
        verbose_name=_('Rate type'),
        choices=RATE_TYPE_CHOICES,
        default=RATE_TYPE_HOURLY,
    )
    rate_detail = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Rate description'),
        help_text=_('Rate description')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Proposal description')
    )
    post = models.ForeignKey(
        PostedMatter,
        on_delete=models.DO_NOTHING,
        verbose_name='Posted Matter',
        related_name='proposals'
    )

    currency = models.ForeignKey(
        Currencies,
        on_delete=models.PROTECT,
        default=1,
        verbose_name=_('Currency'),
        related_name='proposals'
    )

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REVOKED = 'revoked'
    STATUS_CHAT = 'chat'
    STATUS_WITHDRAWN = 'withdrawn'
    STATUS_CLOSED_BY_CLIENT = 'closed by client'

    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACCEPTED, _('Accepted')),
        (STATUS_REVOKED, _('Revoked')),
        (STATUS_CHAT, _('Chat')),
        (STATUS_WITHDRAWN, _('withdrawn')),
        (STATUS_CLOSED_BY_CLIENT, _('closed by client')),
    )

    status = FSMField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_('Status')
    )
    status_modified = models.DateTimeField(
        default=timezone.now,
        help_text=_('Datetime when status was modified'),
        verbose_name=_('Status Modified')
    )
    is_hidden_for_client = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for client')
    )
    is_hidden_for_mediator = models.BooleanField(
        default=False,
        verbose_name=_('Hidden for mediator')
    )
