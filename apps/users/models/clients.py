from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from ..models import querysets
from .users import AppUserHelperMixin
from ...users.models.users import AppUser


__all__ = [
    'AbstractClient',
    'Client',
]


class AbstractClient(BaseModel):
    """ Модель представляет общие поля между приглашением и клиентом.
    Атрибуты:
        client_type (str): Тип клиента (физическое лицо или фирма)
        organization_name (str): Название организации клиента
    """
    INDIVIDUAL_TYPE = 'individual'
    FIRM_TYPE = 'firm'
    TYPES = (
        (INDIVIDUAL_TYPE, _('Individual')),
        (FIRM_TYPE, _('Firm'))
    )

    client_type = models.CharField(
        max_length=50,
        default=INDIVIDUAL_TYPE,
        choices=TYPES,
        verbose_name=_('Type of client'),
        help_text=_('Type of client')
    )

    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name of organization'),
        help_text=_('Name of organization')
    )

    class Meta:
        abstract = True

    def clean_organization_name(self):
        """ Проверьте поле `имя_организации`.
        Проверьте два случая:
            Этот клиент фирмы имеет название organization_name.
            У этого отдельного клиента нет имени organization_name.
        """

        if self.client_type == self.FIRM_TYPE and not self.organization_name:
            raise ValidationError(_(
                'Firm clients must have name of organization'
            ))

    @property
    def is_organization(self) -> bool:
        """ Возвращает значение true, если клиент является `фирмой`. """
        return self.client_type == self.FIRM_TYPE

    @property
    def display_name(self) -> str:
        """ Показать отображаемое имя клиента.
        Если клиент - физическое лицо, мы показываем его полное имя
        Если клиент - фирма, мы показываем название ее организации
        """
        if self.client_type == self.INDIVIDUAL_TYPE:
            return self.full_name
        return self.organization_name


class Client(AppUserHelperMixin, AbstractClient):
    """ Модель определяет информацию о клиенте.
    Модель описывает местоположение клиента (штат США) и описание справки
    это то, что мы ищем.

    Атрибуты:
        user (AppUser): Отношение к AppUser
        job (str): должность клиента
        country (cities_light.Страна): Местонахождение клиента
        state (cities_light.Регион): Местонахождение клиента
        city (cities_light.Город): Местонахождение клиента
        address1 (str): Адрес клиента
        address2 (str): Адрес клиента
        zip code (str): почтовый индекс адреса клиента
        help_description (str): Описание справки, которую ищет клиент
        client (str): Тип клиента (физическое лицо или фирма)
        organization_name (str): Название организации клиента
    """

    user = models.OneToOneField(
        AppUser,
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='client'
    )

    job = models.CharField(
        max_length=128,
        verbose_name=_('Job'),
        help_text=_("Client\'s job title"),
        blank=True,
        null=True
    )

    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        related_name='clients',
        verbose_name=_('Client\'s location(country)'),
        null=True,
        blank=True
    )

    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='clients',
        verbose_name=_('Client\'s location(state)'),
    )

    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        related_name='clients',
        verbose_name=_('Client\'s location(city)'),
        null=True,
        blank=True
    )

    note = models.TextField(
        verbose_name=_('Note'),
        null=True,
        blank=True
    )

    help_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Needed help description'),
        help_text=_('What client is looking for help with')
    )

    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('zip code'),
        help_text=_('Client\'s location(zip code)')
    )

    address1 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Address1'),
        help_text=_('Client\'s location(address1)')
    )

    address2 = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Address2'),
        help_text=_('Client\'s location(address2)')
    )

    shared_with = models.ManyToManyField(
        AppUser,
        related_name='shared_clients',
        verbose_name=_('Shared with'),
        help_text=_('Users with which client is shared')
    )

    favorite_mediators = models.ManyToManyField(
        'Mediator',
        related_name='clients',
        verbose_name='favorite_mediators',
        help_text=_('Favorite mediator of client')
    )

    objects = querysets.ClientQuerySet.as_manager()

    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')

    @classmethod
    def mediator_clients_and_leads(cls, mediator):
        """ Возвращает лиды и клиентов для адвоката """
        # только зацепки
        leads = cls.objects.exclude(
            matters__mediator__in=[mediator.pk],
        ).filter(
            leads__mediator__in=[mediator.pk]
        ).distinct()
        # фактические клиенты с вопросами
        clients = cls.objects.filter(
            matters__mediator__in=[mediator.pk],
        ).distinct()

        return leads | clients

    def contacts(self):
        """ Верните адвокатов, с которыми клиент находится в контакте """
        contacts = set(self.leads.values_list('mediator__user', flat=True))
        contacts |= set(self.leads.values_list('enterprise__user', flat=True))
        contacts |= set(self.matters.values_list('mediator__user', flat=True))
        contacts |= set(self.opportunities.values_list(
            'mediator__user', flat=True
        ))
        return contacts
