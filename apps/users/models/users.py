import uuid
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from djstripe import settings as djstripe_settings
from imagekit import models as imagekitmodels
from imagekit.processors import ResizeToFill, Transpose
from libs import utils
from apps.core.models import BaseModel
from ..models import querysets
from .managers import AppUserManager

__all__ = [
    'AppUser',
    'UserStatistic',
    'AppUserHelperMixin',
]

def upload_user_avatar_to(instance, filename):
    """ Загружайте аватары пользователей в эту папку.
    Возвращается:
        Строка. Сгенерированный путь к изображению.
    """
    return 'users/avatars/{filename}'.format(
        filename=utils.get_random_filename(filename)
    )
    
class AppUser(BaseModel, AbstractBaseUser, PermissionsMixin):
    """ Пользовательская модель пользователя.
    Атрибуты:
        uuid (str): Используется для создания уникальной ссылки для отказа от подписки по 
            электронной почте.
        first_name (str): имя
        middle_name (str): второе имя - необязательно
        last_name (str): фамилия
        email (str): адрес электронной почты (должен быть уникальным), это поле нашего имени 
            пользователя
        phone (str): Номер телефона
        avatar (file): аватар пользователя, обрезанный до размера 300x300 пикселей
        is_staff (bool): определяет, может ли пользователь войти в
            этот сайт администратора
        is_active (bool): указывает, должен ли этот пользователь быть
            рассматривается как активный
        active_subscription (SubscriptionProxy): ссылка на активную текущую подписку.
            объект подписки
        date_joined (datetime): когда пользователь присоединился
        specialities (Speciality): Это поле имеет два значения:
                В случае с адвокатом: в нем перечислены специальности адвоката
                В случае клиента: в нем перечислены специальности, в которых клиенту требуется 
                помощь
        twofa (boolean): флаг для двухфакторной аутентификации
        timezone (TimeZone): внешний ключ к часовому поясу
    """
    # различные возможные типы пользователей в приложении
    USER_TYPE_MEDIATOR = 'mediator'
    USER_TYPE_ENTERPRISE = 'enterprise'
    USER_TYPE_CLIENT = 'client'
    USER_TYPE_SUPPORT = 'support'
    USER_TYPE_STAFF = 'staff'

    USER_TYPES = (
        USER_TYPE_MEDIATOR,
        USER_TYPE_ENTERPRISE,
        USER_TYPE_CLIENT,
        USER_TYPE_SUPPORT,
        USER_TYPE_STAFF,
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        #editable=False,
        verbose_name=_('User uuid'),
        help_text=_(
            'Used to make unique user unsubscribe link'
        )
    )

    first_name = models.CharField(
        _('First name'),
        max_length=100,
    )

    middle_name = models.CharField(
        _('Middle name'),
        max_length=150,
        null=True,
        blank=True,
    )

    last_name = models.CharField(
        _('Last name'),
        max_length=150,
    )

    email = models.EmailField(
        _('E-mail address'),
        unique=True,
    )

    phone = models.CharField(
        max_length=128,
        verbose_name=_('Phone'),
        help_text=_('Phone number'),
        blank=True,
        null=True
    )

    date_joined = models.DateTimeField(
        _('Date joined'),
        default=timezone.now
    )

    is_staff = models.BooleanField(
        _('Staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_subscribed = models.BooleanField(
        _('Subscribed'),
        default=True,
        help_text=(
            'Designates whether the user subscribe email notification'
        )
    )

    active_subscription = models.ForeignKey(
        to='finance.SubscriptionProxy',
        verbose_name=_('Current active subscription'),
        on_delete=models.SET_NULL,
        related_name='appuser',
        null=True,
        blank=True,
        help_text=_(
            'Represents related to user current active stripe subscription'
        ),
    )
    avatar = models.CharField(
        max_length=255,
        verbose_name=_('Avatar'),
        blank=True,
        null=True
    )

    specialities = models.ManyToManyField(
        'Speciality',
        verbose_name=_('Specialities'),
        related_name='users'
    )

    twofa = models.BooleanField(
        _('Two Fator Authentication'),
        default=False,
    )

    onboarding = models.BooleanField(
        _('Onboarding process'),
        default=False,
    )

    timezone = models.ForeignKey(
        'users.Timezone',
        on_delete=models.SET_NULL,
        related_name='users',
        blank=True,
        null=True,
        default=1  # Установите PST по умолчанию
    )

    is_free_subscription = models.BooleanField(
        _('The user is released from the subscription'),
        default=False,
    )

    objects = AppUserManager()

    # таким образом, аутентификация происходит по электронной почте вместо имени пользователя
    USERNAME_FIELD = 'email'

    # Обязательно исключите адрес электронной почты из обязательных полей при проверке 
    # подлинности делается по электронной почте
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('AppUser')
        verbose_name_plural = _('AppUsers')

    def __str__(self):
        if self.full_name:
            return self.full_name
        return self.email

    @property
    def avatar_url(self):
        """ Верните аватар пользователя """
        if self.avatar == '':
            return None
        elif self.avatar is None:
            return None
        return self.avatar

    @property
    def full_name(self):
        """ Верните полное имя пользователя, если оно задано. """
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return None

    @property
    def is_mediator(self):
        """ Проверьте, является ли пользователь адвокатом или нет.
        self.mediator - это ссылка на модель адвоката, определенную в mediators.py .
        """
        return hasattr(self, 'mediator')

    @property
    def is_client(self):
        """ Проверьте, является ли пользователь клиентом или нет.
        self.client - это ссылка на клиентскую модель, определенную в clients.py .
        """
        return hasattr(self, 'client')

    @property
    def is_support(self):
        """ Проверьте, является ли пользователь службой поддержки или нет.
        self.support - это ссылка на модель поддержки, определенную в support.py .
        """
        return hasattr(self, 'support')

    @property
    def is_developer(self):
        """ Пользователь является разработчиком приложения. Используется для проверки разрешений.
        """
        admins = getattr(settings, 'ADMINS', [])
        admin_emails = [email for name, email in admins]
        admin_emails += ['root@root.ru']
        return self.email in admin_emails

    @property
    def is_enterprise_admin(self):
        """ Проверьте, является ли пользователь администратором предприятия или нет
        self.enterprise - это ссылка на модель предприятия, определенную в enterprise.py
        """
        return hasattr(self, 'owned_enterprise') and \
            self.owned_enterprise and \
            self.owned_enterprise.user_id == self.pk

    def is_enterprise_admin_of(self, enterprise_id):
        """ Проверьте, является ли пользователь администратором предприятия или нет
        self.enterprise - это ссылка на модель предприятия, определенную в enterprise.py
        """
        return hasattr(self, 'owned_enterprise') and \
            self.owned_enterprise and \
            str(self.owned_enterprise.id) == enterprise_id

    @property
    def user_type(self):
        """ Возвращает тип пользователя в виде строки. """
        if self.is_client:
            return self.USER_TYPE_CLIENT
        elif self.is_enterprise_admin:
            return self.USER_TYPE_ENTERPRISE
        elif self.is_mediator:
            return self.USER_TYPE_MEDIATOR
        elif self.is_support:
            return self.USER_TYPE_SUPPORT
        return self.USER_TYPE_STAFF

    @property
    def user_type_display(self):
        """ Возвращает значение пользовательского типа `display` в виде строки. """
        from ..models import Support

        # пользователь "службы поддержки" должен быть показан как "Помощник юриста" 
        # во внешнем интерфейсе
        if self.is_support:
            return Support.DISPLAY_NAME
        return self.user_type

    @property
    def display_name(self):
        """ Получите отображаемое имя пользователя. """
        if self.is_client:
            return self.client.display_name
        elif self.is_mediator:
            return self.mediator.display_name
        elif self.is_support:
            return self.support.display_name
        return self.full_name

    @cached_property
    def has_active_subscription(self) -> bool:
        """ Проверьте, есть ли у пользователя активная подписка """
        return self.is_free_subscription | bool(self.active_subscription_id)

    @cached_property
    def customer(self):
        """ Клиент, связанный с возвратом """
        from ...finance.models import CustomerProxy
        customer_count = CustomerProxy.objects.filter(
            subscriber=self,
            livemode=djstripe_settings.STRIPE_LIVE_MODE
        ).count()
        if customer_count > 1:
            raise AttributeError(
                f'More than one stripe customer '
                f'accounts({customer_count}) linked to your app account')
        return CustomerProxy.objects.filter(
            subscriber=self,
            livemode=djstripe_settings.STRIPE_LIVE_MODE
        ).first()

    @property
    def deposit_account(self):
        """ Получить депозитный счет пользователя. """
        from ...finance.models import FinanceProfile
        try:
            return self.finance_profile.deposit_account
        except FinanceProfile.DoesNotExist:
            return None

    @property
    def plan_id(self):
        """ Получить идентификатор плана пользователя """
        try:
            return self.finance_profile.initial_plan.id
        except AttributeError:
            return None

    @property
    def subscribed(self):
        """ Проверьте, подписывается пользователь или нет """
        canceled = True
        if self.customer:
            current_sub = self.customer.current_subscription
            if current_sub.status == 'canceled':
                canceled = False
            elif current_sub.status == 'active' and \
                    current_sub.cancel_at_period_end:
                canceled = False
        else:
            canceled = False
        return canceled

    @property
    def expiration_date(self):
        """ Проверьте, подписывается пользователь или нет """
        expiration_date = None
        from apps.finance.models import SubscriptionProxy

        if self.customer:
            current_sub = self.customer.current_subscription
            if current_sub.status == 'active' and \
                    current_sub.cancel_at_period_end:
                expiration_date = SubscriptionProxy.get_cancel_date(
                    current_sub
                )
        return expiration_date

    @property
    def enterprises_pending(self):
        from apps.users.models import Enterprise, EnterpriseMembers
        invites_to_registered_user = EnterpriseMembers.objects.filter(
            user=self,
            state=EnterpriseMembers.STATE_PENDING
        )
        invites_to_non_registered_user = EnterpriseMembers.objects.filter(
            invitee__email=self.email
        )
        return Enterprise.objects.filter(
            Q(id__in=invites_to_registered_user.values_list(
                'enterprise_id', flat=True)) |
            Q(id__in=invites_to_non_registered_user.values_list(
                'enterprise_id', flat=True))
        )


class AppUserHelperMixin:
    """ Общие свойства для адвокатов, клиентов и моделей поддержки. """

    def __str__(self):
        if hasattr(self, 'user'):
            return str(self.user)
        return 'None'

    def clean_user(self):
        """ Убедитесь, что пользователь еще не является пользователем другого типа. """
        from . import Mediator, Client, Enterprise, Support

        if not hasattr(self, 'user'):
            return

        model_check_map = {
            Mediator: self.user.is_client or self.user.is_support,
            Enterprise: self.user.is_support,
            Client: self.user.is_enterprise_admin or self.user.is_support,
            Support: self.user.is_mediator or self.user.is_client,
        }

        if model_check_map[self._meta.model]:
            raise ValidationError(_(
                f'User {self.user} is already attached to another user type'
            ))

    @property
    def email(self):
        """ Получите адрес электронной почты пользователя. """
        return self.user.email

    @property
    def full_name(self):
        """ Получите полное имя пользователя. """
        return self.user.full_name

    @property
    def display_name(self):
        """ Получите отображаемое имя пользователя. """
        return self.full_name

    @cached_property
    def has_active_subscription(self) -> bool:
        """ Проверьте, есть ли у пользователя активная подписка """
        return self.user.is_free_subscription | bool(self.user.active_subscription_id)

    @cached_property
    def customer(self):
        """ Вернуть связанного клиента. """
        customer_count = CustomerProxy.objects.filter(
            subscriber=self,
            livemode=djstripe_settings.STRIPE_LIVE_MODE
        ).count()
        if customer_count > 1:
            raise AttributeError(
                f'More than one stripe customer '
                f'accounts({customer_count}) linked to your app account')
        return CustomerProxy.objects.filter(
            subscriber=self,
            livemode=djstripe_settings.STRIPE_LIVE_MODE
        ).first()

    @property
    def deposit_account(self):
        """ Получить депозитный счет пользователя. """
        return self.user.deposit_account


class UserStatistic(BaseModel):
    """ Эта модель представляет пользовательскую статистику.
    Он использовался для отслеживания различной статистики пользователей, такой как количество
    конвертированных потенциальных клиентов или возможностей за определенный период времени.
    Атрибуты:
        user (AppUser): Ссылка на владельца статистики (самого пользователя)
        tag (str): Идентификатор статистики или, другими словами, тип статистики,
            используемый для поиска
        count (int): Используется для отслеживания объема статистики (например, для
            20 сентября у пользователя было 17 возможностей)
    """

    user = models.ForeignKey(
        AppUser,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    # Возможности - это темы, созданные пользователями в разделе "Адвокат".
    # юрисдикция и имеют одинаковые категории специализации или содержат ключевые слова в
    # заголовок или в первом сообщении такой же, как у адвоката.
    TAG_OPPORTUNITIES = 'opportunities'
    TAG_OPEN_MATTER = 'open_matter'
    TAG_REFERRED_MATTER = 'referred_matter'
    TAG_CLOSE_MATTER = 'close_matter'
    TAG_ACTIVE_LEAD = 'active_lead'
    # Преобразованный лид - это лид, который был упомянут при создании материи.
    TAG_CONVERTED_LEAD = 'converted_lead'
    TAGS = (
        (TAG_OPPORTUNITIES, _('Opportunities')),
        # (TAG_ACTIVE_MATTER, _('Active matter')),
        (TAG_OPEN_MATTER, _('Open matter')),
        (TAG_REFERRED_MATTER, _('Referred matter')),
        (TAG_CLOSE_MATTER, _('Close matter')),
        (TAG_ACTIVE_LEAD, _('Active lead')),
        (TAG_CONVERTED_LEAD, _('Converted lead')),
    )

    tag = models.CharField(
        max_length=50,
        choices=TAGS,
        verbose_name=_('Tag'),
        help_text=_('Identifier of statistic'),
    )

    count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Count'),
        help_text=_('Count'),
    )

    objects = querysets.UserStatisticsQuerySet.as_manager()

    class Meta:
        verbose_name = _('User statistics')
        verbose_name_plural = _('User statistics')
        indexes = [
            models.Index(fields=('user', 'created',)),
        ]

    def __str__(self):
        return (
            f'Stats for {self.user}. Tag: {self.tag}, Count: {self.count}, '
            f'Date: {self.created}'
        )
