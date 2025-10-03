from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from ...users.models.users import AppUser


class Speciality(BaseModel):
    """ Модель определяет специальность адвокатов.
    В нем описываются области специализации адвокатов
    Примеры:
        Personal Injury
        Corporate
        Tax
        Criminal
        Civil Rights

    Attributes:
        title (str): title of speciality
    """

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        unique=True,
    )
    description = models.TextField(
        verbose_name=_('Description'),
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        AppUser,
        verbose_name=_('Created By'),
        related_name='speciality',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Speciality')
        verbose_name_plural = _('Specialities')

    def __str__(self):
        return self.title


class FeeKind(BaseModel):
    """ Модель определяет вид платы.
    В нем описывается, какие виды гонораров будут рассматривать адвокаты
    Примеры:
        Flat Fee
        Contingency Fee
        Negotiable Fee
        Alternative Fee

    Attributes:
        title (str): title of fee kind
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Fee Kind')
        verbose_name_plural = _('Fee Kinds')

    def __str__(self):
        return self.title


class Jurisdiction(BaseModel):
    """ Модель определяет юрисдикцию.
    Атрибуты:
        region (cities_light.Region): Region
        country (cities_light.Country): Country
        agency (str): information of jurisdiction
    """
    country = models.ForeignKey(
        'cities_light.Country',
        verbose_name=_('Jurisdiction country'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='jurisdiction'
    )

    state = models.ForeignKey(
        'cities_light.Region',
        verbose_name=_('Jurisdiction state'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='jurisdiction'
    )

    city = models.ForeignKey(
        'cities_light.City',
        verbose_name=_('Jurisdiction city'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='jurisdiction'
    )

    agency = models.CharField(
        max_length=100,
        null=True,
        verbose_name=_('Agency')
    )

    number = models.CharField(
        max_length=20,
        null=True,
        verbose_name=_('Registeration number')
    )

    year = models.CharField(
        max_length=4,
        null=True,
        verbose_name=_('Admitted year')
    )

    class Meta:
        verbose_name = _('Jurisdiction')
        verbose_name_plural = _('Jurisdiction')

    def __str__(self):
        return self.agency or ''


class FirmLocation(BaseModel):
    """ Модель определяет местоположение фирмы.
    Атрибуты:
        state (cities_light.Region): State
        country (cities_light.Country): Country
        address (str): Address
        city (str): City
        zip_codes (str): ZipCode
    """
    country = models.ForeignKey(
        'cities_light.Country',
        verbose_name=_('Firm country'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='firm_location'
    )

    state = models.ForeignKey(
        'cities_light.Region',
        verbose_name=_('Firm state'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='firm_location'
    )

    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        verbose_name=_('Firm city'),
        null=True,
        blank=True,
        related_name='firm_location'
    )

    address = models.CharField(
        max_length=100,
        verbose_name=_('Address')
    )

    zip_code = models.CharField(
        max_length=20,
        verbose_name=_('ZipCode')
    )

    class Meta:
        verbose_name = _('FirmLocation')
        verbose_name_plural = _('FirmLocation')

    def __str__(self):
        return self.address


class AppointmentType(BaseModel):
    """ Модель определяет принятые типы назначений.
    В нем описывается, какие типы назначений будут рассматривать адвокаты
    Примеры:
        Личные встречи
        Виртуальные встречи
    Атрибуты:
        title (str): type of appointment
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Appointment Type')
        verbose_name_plural = _('Appointment Type')

    def __str__(self):
        return self.title


class PaymentType(BaseModel):
    """ Модель определяет тип принятого платежа.
    В нем описывается, какие типы платежей рассмотрят адвокаты

    Примеры:
        Прямой дебет(ACH/eCheck)
        Кредитные карты

    Атрибуты:
        название (str): Тип платежа
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Payment Type')
        verbose_name_plural = _('Payment Type')

    def __str__(self):
        return self.title


class Language(BaseModel):
    """ Модель определяет разговорный язык.
    В нем описывается, на каких языках могут говорить адвокаты
    Примеры:
        Английский, русский
    Атрибуты:
        название (str): Языки
    """
    title = models.CharField(
        max_length=50,
        verbose_name=_('Title'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Language')

    def __str__(self):
        return self.title


class Currencies(BaseModel):
    """ Модель определяет валюты
    В нем описывается, в каких валютах адвокаты могут взимать плату
    Примеры:
        USD, GBP, ERU

    Attributes:
        titles (str): Currencies
    """
    title = models.CharField(
        max_length=3,
        verbose_name=_('Currencies'),
        unique=True
    )

    class Meta:
        verbose_name = _('Currencies')
        verbose_name_plural = _('Currencies')

    def __str__(self):
        return self.title


class FirmSize(BaseModel):
    """ Модель определяет размер фирмы
    В нем описывается приблизительное количество членов фирмы
    Примеры:
        2-10, 11-50, 51-100,
    Атрибуты:
        названия (str): Размер фирмы
    """
    title = models.CharField(
        max_length=10,
        verbose_name=_('Firmsize'),
        unique=True
    )

    class Meta:
        verbose_name = _('Firmsize')
        verbose_name_plural = _('Firmsize')

    def __str__(self):
        return self.title


class TimeZone(BaseModel):
    """ Модель определяет часовой пояс
    В нем описаны все данные о часовых поясах
    Примеры:
        (UTC-08:00) по тихоокеанскому времени (США и Канада)
    Атрибуты:
        заголовок(str): Название часового пояса
    """

    title = models.TextField(
        verbose_name=_('Timezone'),
    )

    class Meta:
        verbose_name = _('Timezone')
        verbose_name_plural = _('Timezones')

    def __str__(self):
        return self.title


class LawFirm(BaseModel):
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        unique=True,
    )

    class Meta:
        verbose_name = _('Law Firm')
        verbose_name_plural = _('Law Firms')

    def __str__(self):
        return self.name