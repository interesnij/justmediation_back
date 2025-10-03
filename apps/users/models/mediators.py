import uuid
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models.utils.verification import VerifiedRegistration
from ...finance.services import stripe_subscriptions_service
from . import querysets
from .users import AppUserHelperMixin
from ...users.models.users import AppUser


class Mediator(AppUserHelperMixin, VerifiedRegistration):
    """ Модель описывает образование, опыт, специальность адвоката, гонорары
        и дополнительная информация об адвокате.

        Notes:
        У пользователя может быть только один профиль адвоката.
        Адвокат должен иметь либо номер адвокатской конторы, либо регистрационный номер.
        Мы ориентируем help_text полей на команду интерфейса, а не на пользователей приложения. 
        Причина в том, что drf_yasg использует его для описания полей в сериализаторах.
        После того, как пользователь отправил свой профиль адвоката, его учетная запись становится
        неактивен до тех пор, пока его профиль адвоката не будет одобрен администраторами.
        Мы не используем никаких интеграций с Google map api, все данные о местоположении поступают
        из интерфейса

        Атрибуты:
        user (AppUser): Отношение к AppUser
        verification_status (str):
            Проверка статуса доверенности, существует три статуса:
            not_verified - значение по умолчанию при отправке
            approved - Одобрено администраторами
            denied - Отклонено администраторами
        featured (bool): Если у адвоката есть премиум-подписка, он становится избранным адвокатом
            в поиске клиентов
        sponsored (bool): Если адвокат каким-либо образом спонсируется justmediation, то администратор 
            устанавливает это поле, и этот адвокат появится в специальном месте на главной
            страница сайта. (Это альтернатива избранному)
        sponsor_link (str): Ссылка на спонсора justmediation. Будет использоваться на интерфейсной 
            части.
        followers (AppUser): Пользователи, которые подписаны на адвоката. Они будут получать 
            уведомления о деятельности адвоката 
        firm_name(str): Название фирмы, в которой находится адвокат
        firm_name (url): URL фирмы
        firm_locations (dict): Название страны, штата, города, адреса, почтового индекса, 
            где находится адвокат
        practice_jurisdictions (dict): Название страны, региона, учреждения, в котором 
            находится адвокат
        license_info (str): Штат адвоката, учреждение, дата поступления и членство в коллегии 
            адвокатов номер
        practice_description (str): Описание юридической практики адвоката
        years_of_experience (int): Годы адвокатского стажа
        have_speciality (bool): Есть ли у адвоката специальность
        speciality_time (int): Количество лет практики в специализированной области
        speciality_matters_count (int): Приблизительное количество дел за последние 5 лет, 
            рассмотренных адвокатом в специализированной области
        fee_rate (decimal): Сколько времени занимает адвокат в час
        fee_types (FeeKind): Виды гонораров, принимаемых адвокатом
        extra_info (str): Дополнительная информация об адвокате
        charity_organizations (str): Название любой волонтерской или благотворительной 
            организации, с которой вы работаете или являетесь членом
        keywords (List[str]): Используйте при поиске возможностей адвоката
        is_submittable_potential(boolean): Предложение, подлежащее отправке
            для потенциального клиента
    """
    user = models.OneToOneField(
        AppUser,
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='mediator'
    )

    enterprise = models.ForeignKey(
        'Enterprise',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Enterprise'),
        related_name='mediators'
    )

    followers = models.ManyToManyField(
        AppUser,
        verbose_name=_('Followers'),
        related_name='followed_mediators',
        blank=True
    )

    featured = models.BooleanField(
        default=False,
        verbose_name=_('Is featured')
    )

    biography = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Biography'),
        help_text=_('Mediator\'s legal pratice')
    )

    # Sponsor information

    sponsored = models.BooleanField(
        default=False,
        verbose_name=_('Is sponsored'),
        help_text=_('Is mediator sponsored justmediation')
    )

    sponsor_link = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Sponsor link'),
        help_text=_('Link to the sponsor of justmediation')
    )

    # Location

    firm_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Firm name'),
        help_text=_('Firm Name')
    )

    website = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Firm website'),
        help_text=_('Firm website url')
    )

    firm_locations = models.ManyToManyField(
        'FirmLocation',
        related_name='mediators',
        verbose_name=_('Firm Location'),
        help_text=_(
            'Country, State(s), Address(s), City(s), Zipcode '
            'of mediator\'s Firm'
        ),
        blank=True
    )

    # Practice

    practice_jurisdictions = models.ManyToManyField(
        'Jurisdiction',
        related_name='mediators',
        verbose_name=_('Practice jurisdictions'),
        help_text=_(
            'Country, State(s), Agency(s) or federal jurisdiction mediator'
            ' are licensed or authorised to practice in'
        ),
        blank=True
    )

    license_info = models.TextField(
        verbose_name=_('Licence info'),
        help_text=_(
            "Mediator's state, agency, date of admission "
            "and bar membership number"
        ),
        blank=True
    )

    practice_description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=_('Practice description'),
        help_text=_(
            'Description of mediator\'s legal practice (1000 characters)'
        )
    )

    years_of_experience = models.PositiveIntegerField(
        validators=(
            MaxValueValidator(100),
        ),
        verbose_name=_('How long has mediator been practicing'),
        default=0
    )

    # Speciality

    have_speciality = models.BooleanField(
        default=True,
        verbose_name=_('Have speciality'),
        help_text=_(
            'Does mediator have speciality'
        )
    )

    speciality_time = models.PositiveIntegerField(
        validators=(
            MaxValueValidator(100),
        ),
        null=True,
        blank=True,
        verbose_name=_('Speciality time'),
        help_text=_('Numbers of years practiced in specialized area')
    )

    speciality_matters_count = models.PositiveIntegerField(
        verbose_name=_('Speciality matters count'),
        null=True,
        blank=True,
        help_text=_(
            'Approximate number of matters in last 5 years, handled by '
            'mediator in specialized area'
        )
    )

    # Service Fees

    fee_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Fee rate'),
        help_text=_('How much mediator take per hour'),
        null=True,
        default=None
    )

    fee_types = models.ManyToManyField(
        'FeeKind',
        verbose_name=_('FeeKinds'),
        related_name='mediators',
        blank=True
    )

    appointment_type = models.ManyToManyField(
        'AppointmentType',
        verbose_name=_('AppointmentTypes'),
        related_name='mediators',
        blank=True
    )

    payment_type = models.ManyToManyField(
        'PaymentType',
        verbose_name=_('PaymentType'),
        related_name='mediators',
        blank=True
    )

    spoken_language = models.ManyToManyField(
        'Language',
        blank=True,
        verbose_name=_('SpokenLanguages'),
        related_name='mediators'
    )

    fee_currency = models.ForeignKey(
        'Currencies',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Fee Currency'),
        related_name='mediators'
    )

    # Additional information

    extra_info = models.TextField(
        verbose_name=_('Extra information'),
        null=True,
        blank=True,
        help_text=_('Extra information about mediator')
    )

    charity_organizations = models.TextField(
        verbose_name=_('Charity organizations'),
        null=True,
        blank=True,
        help_text=_(
            'Name of any volunteer or charitable organizations mediator work'
            'with or are member of'
        )
    )

    keywords = ArrayField(
        models.CharField(max_length=255),
        default=list,
        verbose_name=_('Keywords'),
        help_text=_(
            'Based on keywords, opportunities are formed for mediator'
        ),
        blank=True
    )

    is_submittable_potential = models.BooleanField(
        default=False,
        verbose_name=_('Is Submittable Potential'),
        help_text=_(
            'Sumbit proposals for potential client engagments'
        )
    )

    industry_contacts = models.ManyToManyField(
        AppUser,
        related_name='contacted_mediator',
        verbose_name=_('Industry Contacts'),
        through='MediatorIndustryContacts',
        blank=True
    )

    # tax
    tax_rate = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        verbose_name=_('Tax rate'),
        help_text=_('Tax rate'),
        null=True,
        default=None
    )

    objects = querysets.MediatorQuerySet.as_manager()

    class Meta:
        verbose_name = _('Mediator')
        verbose_name_plural = _('Mediators')

    def clean_sponsor_link(self):
        """ Убедитесь, что ссылка есть только у спонсируемого адвоката. """
        if self.sponsor_link and not self.sponsored:
            raise ValidationError(_(
                'Only sponsored mediators can have sponsored links'
            ))

    def post_verify_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки".
        Добавьте создание "платной" подписки, если stripe включена.
        """
        # Например, локальное развитие не требует создания
        # подписка на stripe
        if settings.STRIPE_ENABLED:
            stripe_subscriptions_service.create_initial_subscription(
                user=self.user,
                trial_end=kwargs['trial_end']
            )

    def post_verify_by_admin_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки".
        После успешной  верификации пользователя администратором отправьте "mediator_verified"
        сигнал.
        """
        from ..signals import mediator_verified
        mediator_verified.send(
            sender=self.user._meta.model,
            instance=self.user
        )


class MediatorIndustryContacts(models.Model):
    mediator = models.ForeignKey(
        'Mediator',
        on_delete=models.CASCADE,
        verbose_name=_('Mediator')
    )
    industry_contact = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        verbose_name=_('Industry Contact')
    )
    chat_channel = models.UUIDField(
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
        unique=True,
    )
