import uuid as uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from ..models import querysets
# from .clients import AbstractClient
from .users import AppUser


__all__ = [
    'Invite',
]


class Invite(BaseModel):
    """ Модель определяет приглашения разных пользователей из приложения.
    Он используется в случаях, когда адвокат и другой пользователь (клиент или поверенный) 
    встречаются за пределами сайта, и адвокат хочет работать с ним через приложение.

    Существуют следующие возможные типы приглашений:
        - адвокат приглашает клиента, должны быть заполнены поля `first_name`,
            `last_name`, `email`, `сообщение`, `приглашающий` (`invited_by_user` тип).
        - адвокат приглашает другого адвоката из `share matter`, там должно быть
            должны быть заполнены поля "электронная почта", "заголовок", "сообщение", "вопрос", 
            "приглашающий". Так когда адвокат зарегистрирован и верифицирован - он получит 
            электронное письмо о том, что с ним поделились каким-то вопросом (тип `invited_by_user`).
        - импортировано пользователями из других источников (веб-сайт WordPress), там должно быть
            должны быть заполнены `email`, `first_name`, `last_name`, `specialties`, `phone`,
            `help_description` (тип "импортированный").

    Атрибуты:
        uuid (str): Первичный ключ приглашения, используемый для создания уникальной ссылки 
        на приглашение в сообщении электронной почты.
        inviter (AppUser): Адвокат, создавший приглашение.
        user (AppUser): Если приглашенное лицо примет это приглашение, мы сохраним нового
            зарегистрированного пользователя.
        user_type (str): Типом приглашенного пользователя может быть
                            client
                            mediator
                            lead
        type (str):
            Введите в приглашении
            invited_by_user - создан с помощью api
            imported - создано с помощью django import export
        first_name (str): Имя приглашенного пользователя.
        middle_name (str): Второе имя приглашенного контакта - необязательно
        last_name (str): Фамилия приглашенного пользователя.
        mail (str): электронная почта приглашенного пользователя.
        message (str): Сообщение с приглашением - необязательно
        sent (datetime): Время, когда было отправлено приглашение.
        note (str): Адвокат может добавить любое примечание, связанное с клиентом. - необязательно
        zip_code (str): почтовый индекс приглашенного контакта - необязательно
        address (str): Адрес приглашенного контактного лица - необязательно
        countru (str): Страна приглашенного контактного лица - необязательно
        state (str): Штат приглашенного контактного лица - необязательно
        city (str): Город приглашенного контактного лица - необязательно
        role (str): Роль приглашенного контактного лица - необязательно

        client_type (str): Тип клиента (клиент или потенциальный клиент)
        organization_name (str): Название организации приглашаемого

        Дополнительная информация из пользовательского интерфейса sharing matters:
        title (str): Название приглашения
        matter (Matter): вопрос, которым можно будет поделиться после регистрации пользователя

        Дополнительная информация из WordPress:
        specialities (Speciality): Список фирменных блюд, выбранных в WordPress
        help_description (str): Описание справки в WordPress
        phone (str): Телефон, указанный в WordPress

    """
    CLIENT_TYPE_CLIENT = 'client'
    CLIENT_TYPE_LEAD = 'lead'
    CLIENT_TYPE_MEDIATOR = 'mediator'
    TYPES = (
        (CLIENT_TYPE_CLIENT, _('client')),
        (CLIENT_TYPE_LEAD, _('lead')),
        (CLIENT_TYPE_MEDIATOR, _('mediator')),
    )
    client_type = models.CharField(
        max_length=50,
        choices=TYPES,
        null=True,
        blank=True,
        verbose_name=_('Type of invitee'),
        help_text=_('Type of invitee')
    )
    uuid = models.UUIDField(
        primary_key=True,
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('UUID'),
        help_text=_(
            'Primary key of invitation, used to make unique invitation link'
        )
    )

    inviter = models.ForeignKey(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Inviter'),
        related_name='sent_invitations',
        null=True
    )

    user = models.ForeignKey(
        AppUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        related_name='invitations'
    )
    

    USER_TYPE_CLIENT = 'client'
    USER_TYPE_MEDIATOR = 'mediator'
    USER_TYPE_LEAD = 'lead'
    USER_TYPES = (
        (USER_TYPE_CLIENT, _('Client')),
        (USER_TYPE_MEDIATOR, _('mediator')),
        (USER_TYPE_LEAD, _('Lead')),
    )

    user_type = models.CharField(
        max_length=10,
        default=USER_TYPE_CLIENT,
        choices=USER_TYPES,
        verbose_name=_('Type of invited user')
    )
    note = models.TextField(
        verbose_name=_('Note'),
        null=True,
        blank=True
    )
    TYPE_IMPORTED = 'imported'
    TYPE_INVITED = 'invited_by_user'
    TYPES = (
        (TYPE_IMPORTED, _('Imported')),
        (TYPE_INVITED, _('Invited by user')),
    )

    type = models.CharField(
        max_length=20,
        default=TYPE_INVITED,
        choices=TYPES,
        verbose_name=_('Type of invitation')
    )

    first_name = models.CharField(
        verbose_name=_('First name'),
        max_length=100,
    )

    last_name = models.CharField(
        verbose_name=_('Last name'),
        max_length=150,
    )

    middle_name = models.CharField(
        verbose_name=_('Middle name'),
        max_length=150,
        null=True,
        blank=True
    )

    email = models.EmailField(
        verbose_name=_('E-mail address'),
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Message of invitation'),
        null=True,
        blank=True
    )

    sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent at'),
        help_text=_('Time when invitation was sent')
    )

    # Extra information from sharing matters UI

    title = models.CharField(
        max_length=256,
        verbose_name=_('Title'),
        help_text=_('Title'),
        blank=True,
        null=True
    )

    #matter = models.ForeignKey(
    #    'business.Matter',
    #    null=True,
    #    blank=True,
    #    on_delete=models.SET_NULL,
    #    verbose_name=_('Matter'),
    #    related_name='invitations'
    #)
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_('zip code'),
        help_text=_('Invited contact\'s location(zip code)')
    )

    address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Address1'),
        help_text=_('Invited contact\'s location(address1)')
    )
    state = models.ForeignKey(
        'cities_light.Region',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contacts_state',
        verbose_name=_('State'),
        help_text=_('Invited contact\'s state')
    )
    country = models.ForeignKey(
        'cities_light.Country',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contacts_country',
        verbose_name=_('Country'),
        help_text=_('Invited contact\'s country')
    )
    city = models.ForeignKey(
        'cities_light.City',
        on_delete=models.SET_NULL,
        verbose_name=_('City'),
        null=True,
        blank=True,
        related_name='contacts_city'
    )
    role = models.CharField(
        max_length=128,
        verbose_name=_('role'),
        help_text=_("Invited contact\'s job title"),
        blank=True,
        null=True
    )

    # Extra information from WordPress for imported users

    specialities = models.ManyToManyField(
        'Speciality',
        verbose_name=_('Specialities'),
        related_name='invites'
    )

    help_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Needed help description'),
        help_text=_('What client is looking for help with')
    )

    phone = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_('Phone'),
        help_text=_("Invite's phone number"),
    )

    shared_with = models.ManyToManyField(
        AppUser,
        related_name='shared_invitees',
        verbose_name=_('Shared with'),
        help_text=_('Users with which invitee is shared')
    )

    organization_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Name of organization'),
        help_text=_('Name of organization')
    )

    objects = querysets.InviteQuerySet.as_manager()

    class Meta:
        verbose_name = _('Invitation')
        verbose_name_plural = _('Invitations')
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'inviter'],
                name='email_inviter_unique'
            )
        ]

    def __str__(self):
        return (
            f'{self.inviter}\'s invitation '
            f'for {self.first_name} {self.last_name}'
        )

    @property
    def full_name(self):
        """ Получите полное имя приглашенного пользователя. """
        if self.user:
            return self.user.full_name
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return None

    def clean_email(self):
        """ Убедитесь, что пользователь с электронной почтой, указанной в приглашении, 
        не существует. """
        user_in_db = AppUser.objects.filter(email__iexact=self.email).first()
        if not self.user and user_in_db:
            raise ValidationError(
                'User with such email is already registered',
                params={
                    'user_pk': user_in_db.pk,
                    'user_type': user_in_db.user_type
                }
            )

    @classmethod
    def get_pending_mediator_invites(cls, mediator):
        """ Возвращает отложенные приглашения для данного адвоката. """
        return cls.objects.filter(
            inviter=mediator.user,
            user__isnull=True,
            user_type__in=[cls.USER_TYPE_CLIENT, cls.USER_TYPE_LEAD]
        )
    @classmethod
    def get_pending_mediator_invites_for_industry_contacts(cls, mediator):
        return cls.objects.filter(
            inviter=mediator.user,
            user__isnull=True,
            user_type__in=[cls.USER_TYPE_MEDIATOR, cls.USER_TYPE_MEDIATOR]
        )
