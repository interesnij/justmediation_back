import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from ...core.models import BaseModel
from .querysets import VideoCallQuerySet
from ...users.models.users import AppUser
from ...users.models.mediators import Mediator


__all__ = (
    'Attachment',
    'Stage',
    'ChecklistEntry',
    'VideoCall',
)

class Attachment(BaseModel):
    """ Модель представляет собой вложения (file) в библиотеке.
    Атрибуты:
        mime_type (str): Mime-тип файла
        file (str): файл документа в хранилище
    """

    mime_type = models.CharField(
        max_length=255,
        verbose_name=_('Mime type'),
        help_text=_('Mime type of file')
    )
    file = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('File'),
        help_text=_("Document's file")
    )

    def __str__(self):
        return self.file.name


class Stage(BaseModel):
    """Модель определяет индивидуальные этапы рассмотрения дел адвокатами.

    Адвокат может создать для себя несколько пользовательских этапов и настроить их по своему усмотрению.
    вопросы.

    Атрибуты:
        mediator (Mediator): Ссылка на владельца сцены (mediator)
        title (str): название этапа
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз
    """

    mediator = models.ForeignKey(
        Mediator,
        on_delete=models.PROTECT,
        verbose_name=_('Mediator'),
        related_name='stages'
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )

    class Meta:
        verbose_name = _('Stage')
        verbose_name_plural = _('Stages')

    def __str__(self):
        return self.title

    @classmethod
    def create_default_stages(cls, mediator):
        cls.objects.create(mediator=mediator, title='Discovery')
        cls.objects.create(mediator=mediator, title='Trial')


class ChecklistEntry(BaseModel):
    """ Модель ChecklistEntry.

    Эта модель представляет собой записи контрольного списка. Это использовалось, когда 
    адвокат пытался закрыть дело. Адвокат просматривает этот контрольный список, и если 
    все записи проверены (на интерфейсной части) адвокат может закрыть дело.
    Атрибуты:
        mediator (Mediator): Владелец записи в контрольном списке
        описание (str): Описание контрольного списка

    """
    mediator = models.ForeignKey(
        Mediator,
        verbose_name=_('Mediator'),
        related_name='checklist',
        on_delete=models.PROTECT
    )

    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Description of checklist')
    )

    class Meta:
        verbose_name = _('Checklist Entry')
        verbose_name_plural = _('Checklist Entries')
        unique_together = ('mediator', 'description')

    def __str__(self):
        return self.description

    def clean_description(self):
        """ Убедитесь, что запись в контрольном списке имеет уникальное описание. """
        duplicate = self.__class__.objects.filter(
            description=self.description, mediator_id=self.mediator_id,
        ).exclude(pk=self.pk)
        if duplicate.exists():
            raise ValidationError(
                f'Entry with same description:`{self.description}` '
                f'is already exist'
            )


class VideoCall(BaseModel):
    """ VideoCall.
    Эта модель представляет собой видеозвонки в jitsi. Адвокат или клиент могут создать
    видеовызов, после его создания все приглашенные пользователи получат
    уведомления.

    Атрибуты:
        call_id (str):
            Идентификатор встречи в jitsi (он использовался для создания ссылки)
            Пример:
                https://meet.jit.si /{call_id}
        participants (AppUser): Приглашенные создателем пользователи
    """
    
    VIDEO_CALL_BASE_URL = 'https://meet.jit.si/'
    MAX_PARTICIPANTS_COUNT = 10

    call_id = models.UUIDField(
        #editable=False,
        unique=True,
        default=uuid.uuid4,
        verbose_name=_('Id of call'),
        help_text=_('Id of call(name of room in jitsi)'),
    )

    participants = models.ManyToManyField(
        AppUser,
        verbose_name=_('Participants'),
        related_name='video_calls',
    )

    objects = VideoCallQuerySet.as_manager()

    class Meta:
        verbose_name = _('Video Call')
        verbose_name_plural = _('Video Calls')

    def __str__(self):
        return f'Video call @ {self.call_id}'

    @property
    def call_url(self) -> str:
        """ Получите полный URL-адрес вызова. """
        return (
            f'{self.VIDEO_CALL_BASE_URL}{self.call_id}'
            # этот идентификатор части добавлен для того, чтобы мобильные телефоны не 
            # просили установить jitsi
            '#config.disableDeepLinking=true'
        )


class Referral(BaseModel):
    """ Referral
    Эта модель представляет собой запрос о передаче дела от другого адвоката
    Атрибуты:
        mediator (Mediator): Referred mediator
        message (str): Message from mediator
    """
    mediator = models.ForeignKey(
        Mediator,
        verbose_name=_('Mediator'),
        related_name='referral',
        on_delete=models.PROTECT
    )
    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Referral message'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Referral')
        verbose_name_plural = _('Referrals')

    def __str__(self):
        return f'Referred from {self.mediator}'


class PaymentMethods(BaseModel):
    """ PaymentMethods
    Эта модель представляет доступные способы оплаты счета-фактуры
    Атрибуты:
        название (str): название способов оплаты
    """
    title = models.CharField(
        max_length=30,
        verbose_name=_('Title'),
        help_text=_('Payment methods'),
    )

    class Meta:
        verbose_name = _('PaymentMethod')
        verbose_name_plural = _('PaymentMethods')

    def __str__(self):
        return self.title
