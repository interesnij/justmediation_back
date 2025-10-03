from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit import models as imagekitmodels
from imagekit.processors import ResizeToFill, Transpose
from libs import utils
from apps.users.models.utils.verification import VerifiedRegistration
from . import querysets
from .users import AppUserHelperMixin
from ...users.models.users import AppUser


def upload_user_avatar_to(instance, filename):
    """ Загружайте аватары пользователей в эту папку.
    Возвращается:
        Строка. Сгенерированный путь к изображению.
    """
    return 'users/avatars/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )

class Enterprise(AppUserHelperMixin, VerifiedRegistration):
    """ Модель определяет информацию о предприятии.
    Модель описывает размер фирмы предприятия, местоположение фирмы, членов
    и дополнительная информация о предприятии.

    Атрибуты:
        user (AppUser): Отношение к AppUser
        role (str): Укажите свою роль
        verification_status (str): есть три статуса:
                not_verified - значение по умолчанию при отправке
                approved - Одобрено администраторами
                denied - Отклонено администраторами
        featured (bool):
            Если у enterprise есть премиум-подписка, она становится полнофункциональной
            предприятие по поиску клиентов
        followers (AppUser): Пользователи, которые подписаны на enterprise. 
            Они будут получать уведомления о деятельности предприятия 
        firm_name(str): Название фирмы, в которой расположено предприятие
        firm_size(str): Размер фирмы
        firm_locations (dict): Название страны, штата, города, адреса, почтового индекса, 
            где находится предприятие расположенный
        team_members (Member): Список участников в enterprise
    """

    ROLE_MEDIATOR = 'Mediator'

    user = models.OneToOneField(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Enterprise Admin'),
        related_name='owned_enterprise',
        default=None
    )

    team_logo = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_('Firm logo'),
        help_text=_('Firm logo')
    )

    role = models.CharField(
        max_length=20,
        verbose_name=_('Enterprise Role'),
        help_text=_("Enterprise Role")
    )

    followers = models.ManyToManyField(
        AppUser,
        verbose_name=_('Followers'),
        related_name='followed_enterprise'
    )

    featured = models.BooleanField(
        default=False,
        verbose_name=_('Is featured')
    )

    # Location

    firm_name = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Firm name'),
        help_text=_('Firm Name')
    )

    firm_size = models.ForeignKey(
        'FirmSize',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enterprise',
        verbose_name=_('Firm size'),
        help_text=_('Firm size'),
    )

    firm_locations = models.ManyToManyField(
        'FirmLocation',
        related_name='enterprise',
        verbose_name=_('Firm Location'),
        help_text=_(
            'Country, State(s), Address(s), City(s), Zipcode '
            'of enterprise\'s Firm'
        )
    )

    team_members_invited = models.ManyToManyField(
        'Member',
        through='EnterpriseMembers',
        related_name='enterprises',
        verbose_name=_('Team Members Invited'),
        help_text=_(
            'Email of enterprise members invited'
        )
    )

    team_members_registered = models.ManyToManyField(
        AppUser,
        through='EnterpriseMembers',
        related_name='enterprises',
        verbose_name=_('Team Members Registered'),
        help_text=_(
            'App User of enterprise members registered'
        )
    )

    objects = querysets.EnterpriseQuerySet.as_manager()

    class Meta:
        verbose_name = _('Enterprise')
        verbose_name_plural = _('Enterprise')

    def post_verify_by_admin_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки".
        После успешной проверки пользователя администратором отправьте
        сигнал "enterprise_verified`.
        """
        from ..signals import enterprise_verified
        enterprise_verified.send(
            sender=self.user._meta.model,
            instance=self.user
        )
