from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from ..core.models import BaseModel
from ..notifications import querysets
from ..users.models.users import AppUser


class Notification(BaseModel):
    """ Модель определяет уведомление пользователя.
    Существует несколько примеров уведомлений, которые пользователи могут получать:
        * Новое сообщение в чате
        * Новое действие в теме, за которым следит пользователь
        * Уведомления об адвокатской деятельности, за которыми следит пользователь
        * Уведомления о проблемах пользователей (например, о новом сообщении, обновлении статуса,
          общий доступ к файлу)
        * Уведомления о том, предоставлен ли доступ к контакту пользователю (адвокату)
    Пользователь может выбрать, как он будет получать уведомления: по электронной почте, 
    посредством push-уведомления или и тем, и другим способом.

    Атрибуты:
        тип (NotificationType): Тип уведомления.
        название (str): Название уведомления.
        extra_payload (dict): Дополнительная полезная нагрузка уведомления, используемая для сохранения
        данные уведомления, которые мы не можем сохранить в content_object.
        content_type (базовая модель): тип содержимого, относящегося к уведомлению
        object_id (int): идентификатор объекта содержимого
        content_object (базовая модель):
            Ссылка на объект, который вызвал уведомление, также используется при
            генерации сообщения об уведомлении, без него(когда равно None),
            уведомление становится избыточным и должно быть удалено

    """

    type = models.ForeignKey(
        'NotificationType',
        on_delete=models.PROTECT,
        verbose_name=_('Notification type'),
        related_name='notifications',
    )

    title = models.CharField(
        verbose_name=_('Title'),
        help_text=_('Title of notification'),
        max_length=255,
    )

    extra_payload = JSONField(
        default=dict,
        verbose_name=_(
            'Extra notification payload'
        ),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50, db_index=True)
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return f'Notification {self.title}'


class NotificationDispatch(BaseModel):
    """Defines many to many relationship between Notification and AppUser.

    This is used to keep track of actually dispatched notifications to users
    and to keep track of if notification is read or not.

    Attributes:
        notification (Notification): Link to notification.
        recipient (AppUser): User, who received notification.
        status (str): Notification status for recipient: prepared, sent, read.

    """
    notification = models.ForeignKey(
        'Notification',
        on_delete=models.CASCADE,
        #editable=False,
        verbose_name=_('Notification'),
        related_name='notification_dispatches',
    )

    recipient = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        #editable=False,
        verbose_name=_('Recipient'),
        related_name='notification_dispatches',
    )

    sender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        #editable=False,
        null=True,
        blank=True,
        verbose_name=_('Sender'),
        related_name='notification_dispatches_sender',
    )

    STATUS_PREPARED = 'prepared'
    STATUS_SENT = 'sent'
    STATUS_READ = 'read'

    STATUSES = (
        (STATUS_PREPARED, _('Prepared')),
        (STATUS_SENT, _('Sent')),
        (STATUS_READ, _('Read'))
    )

    status = FSMField(
        default=STATUS_PREPARED,
        choices=STATUSES,
        verbose_name=_('Status of notification'),
        help_text=_('Notification status for recipient: prepared, sent, read')
    )

    objects = querysets.NotificationDispatchQuery.as_manager()

    class Meta:
        verbose_name = _('Notification dispatch')
        verbose_name_plural = _('Notification dispatches')

    def __str__(self):
        return (
            f'Notification dispatch for {self.recipient} '
            f'of notification: {self.notification}'
        )

    @transition(
        field=status,
        source=STATUS_PREPARED,
        target=STATUS_SENT
    )
    def send(self):
        """Mark notification dispatch as sent."""

    @transition(
        field=status,
        source=(STATUS_PREPARED, STATUS_SENT),
        target=STATUS_READ
    )
    def read(self):
        """Mark notification dispatch as read."""

    @transition(
        field=status,
        source=STATUS_READ,
        target=STATUS_SENT
    )
    def unread(self):
        """Mark notification dispatch as sent(unread notification)."""


class NotificationType(BaseModel):
    """ Модель определяет типы уведомлений.
    Примеры:
        * Новые чаты
        * Новые события
        * Активность на форуме
        * Обновление статуса
        * И т.д.

    Атрибуты:
        группа (Notification Group): Группа, к которой принадлежит тип уведомления.
        runtime_tag (str):
            Название типа уведомления, связанное с кодом. Используется для идентификации
            уведомления за счет использования более удобочитаемых имен в коде.
            Пример: `new_group_chat`
        название (str):
            Описание типа уведомления, которое будет отображаться пользователям. Или
            другими словами, "Удобочитаемое имя типа`
        получатель_тип (str):
            Описывает тип получателя уведомлений. Это может быть:
                * Все
                * Клиент
                * Адвокат
        описание (str): Подробное описание типа уведомления
    """

    group = models.ForeignKey(
        'NotificationGroup',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Notification group'),
        related_name='types',
    )

    runtime_tag = models.CharField(
        unique=True,
        max_length=50,
        #editable=False,
        verbose_name=_('Runtime tag'),
        help_text=_('Code related name of notification type'),
    )

    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        help_text=_(
            'Human-readable name of a type'
        ),
    )

    RECIPIENT_TYPE_CLIENT = 'client'
    RECIPIENT_TYPE_MEDIATOR = 'mediator'
    RECIPIENT_TYPE_ENTERPRISE = 'enterprise'
    RECIPIENT_TYPE_ALL = 'all'

    is_for_client = models.BooleanField(
        default=False,
        verbose_name=_('Is for client'),
        help_text=_('Is notification type available for client')
    )

    is_for_mediator = models.BooleanField(
        default=False,
        verbose_name=_('Is for mediator'),
        help_text=_('Is notification type available for mediator')
    )

    is_for_enterprise = models.BooleanField(
        default=False,
        verbose_name=_('Is for enterprise'),
        help_text=_('Is notification type available for enterprise')
    )

    is_for_other = models.BooleanField(
        default=False,
        verbose_name=_('Is for other'),
        help_text=_('Is notification type available for other')
    )

    is_for_support = models.BooleanField(
        default=False,
        verbose_name=_('Is for support'),
        help_text=_('Is notification type available for support')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        null=True
    )

    objects = querysets.NotificationTypeQuerySet.as_manager()

    class Meta:
        verbose_name = _('Notification type')
        verbose_name_plural = _('Notification types')

    def __str__(self):
        return f'Notification type: {self.title}'

    @property
    def recipient_type(self):
        """Support old versions of app."""
        if self.is_for_mediator:
            return self.RECIPIENT_TYPE_MEDIATOR
        elif self.is_for_client:
            return self.RECIPIENT_TYPE_CLIENT
        elif self.is_for_enterprise:
            return self.RECIPIENT_TYPE_ENTERPRISE
        return self.RECIPIENT_TYPE_ALL


class NotificationGroup(BaseModel):
    """ Модель определяет группы уведомлений.
    Это используется для группировки связанных типов уведомлений. Например, мы группируем
    такие типы уведомлений, как "Новое сообщение", "Обновление статуса" и
    "Общий доступ к файлу", отправляются в группу под названием "Вопросы`.

    Атрибуты:
    title (str):
    Название группы уведомлений, которое будет отображаться для пользователей.
    """
    title = models.CharField(
        max_length=100,
        verbose_name=_('Title'),
        help_text=_(
            'Notification group title which will be displayed for the users'
        )
    )

    class Meta:
        verbose_name = _('Notification group')
        verbose_name_plural = _('Notification groups')

    def __str__(self):
        return f'Notification group: {self.title}'


class NotificationSetting(BaseModel):
    """Model defines notification's settings(for type) for user.

    User can set how does it wish to receive notifications:
        * By email
        * By both
        * By chats
        * By matters
        * By forums
        * By contacts

    Attributes
        user (AppUser): Link to AppUser
        by_email (bool): Is notification send by email
        by_push (bool): Is notification send by push
        by_chats (bool): Is notification send by chats
        by_matters (bool): Is notification send by matters
        by_forums (bool): Is notification send by forums
        by_contacts (bool): Is notification send by contacts

    """
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        #editable=False,
        verbose_name=_('User'),
        related_name='notifications_settings',
    )
    by_email = models.BooleanField(
        default=True,
        verbose_name=_('Notify by email'),
        help_text=_('Notify user by email')
    )
    by_push = models.BooleanField(
        default=True,
        verbose_name=_('Notify by push notification'),
        help_text=_('Notify user by push notification')
    )
    by_chats = models.BooleanField(
        default=True,
        verbose_name=_('Notify for chat'),
        help_text=_('Notify user for chat')
    )
    by_matters = models.BooleanField(
        default=True,
        verbose_name=_('Notify for matter'),
        help_text=_('Notify user for matter')
    )
    by_forums = models.BooleanField(
        default=True,
        verbose_name=_('Notify for forum'),
        help_text=_('Notify user for forum')
    )
    by_contacts = models.BooleanField(
        default=True,
        verbose_name=_('Notify for contact'),
        help_text=_('Notify user for contact')
    )

    class Meta:
        verbose_name = _('Notification setting')
        verbose_name_plural = _('Notification settings')

    def __str__(self):
        return (
            f'{self.user}\'s notification settings '
        )
