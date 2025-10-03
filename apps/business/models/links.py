import mimetypes
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from ...core.models import BaseModel
from ...users.models.users import AppUser
from . import Attachment, querysets

__all__ = (
    'Activity',
    'Note',
    'VoiceConsent',
    'MatterSharedWith'
)

def upload_voice_consents_to(instance, filename: str) -> str:
    """ Загрузите голосовое согласие в папку "Голосовые согласия".
    Аргументы:
        instance (Голосовое согласие): экземпляр модели voice_consent
        filename (str): имя файла голосовых согласий
    Возвращается:
        str: Сгенерированный путь к файлу голосового согласия.
    """
    return 'public/voice_consents/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )

class Activity(BaseModel):
    """ Activity

    Эта модель представляет события ("действия"), которые произошли во фрейме
    по этому вопросу (например: "Отправлен ежемесячный счет-фактура", 
    "Предоставлен расчетный лист к Эбби` и т.д.).

    Атрибуты:
        matter (Matter): это материя, ради которой была произведена деятельность.
        title (str): имя/заголовок созданного действия
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    matter = models.ForeignKey(
        'Matter',
        # деятельность не имеет смысла без соответствующего содержания
        on_delete=models.CASCADE,
        related_name='activities'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Title which describes current activity')
    )
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True
    )

    ACTIVITY_TYPE_MESSAGE = 'message'
    ACTIVITY_TYPE_DOCUMENT = 'document'
    ACTIVITY_TYPE_NOTE = 'note'
    ACTIVITY_TYPE_INVOICE = 'invoice'
    ACTIVITY_TYPE_BILLING_ITEM = 'billing_item'

    ACTIVITY_TYPE_CHOICES = (
        (ACTIVITY_TYPE_MESSAGE, _('Message')),
        (ACTIVITY_TYPE_DOCUMENT, _('Document')),
        (ACTIVITY_TYPE_NOTE, _('Note')),
        (ACTIVITY_TYPE_INVOICE, _('Invoice')),
        (ACTIVITY_TYPE_BILLING_ITEM, _('Billing item')),
    )

    type = models.CharField(
        max_length=25,
        verbose_name=_('Activity type'),
        choices=ACTIVITY_TYPE_CHOICES,
        null=True,
        blank=True,
        default=None,
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')

    def __str__(self):
        return self.title


class Note(BaseModel):
    """Note

    Атрибуты:
        matter (Matter): это вопрос, к которому пользователь добавил заметку 
            (некоторую информацию для него)
        title (str): краткое описание, сокращенное название заметки
        text (text): полный текст примечания
        created_by (AppUser): автор заметки
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    matter = models.ForeignKey(
        'Matter',
        on_delete=models.CASCADE,
        related_name='notes',
    )
    client = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='notes_client',
        null=True
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    text = models.TextField(
        verbose_name=_('Text'),
    )
    created_by = models.ForeignKey(
        AppUser,
        verbose_name=_('Created by'),
        help_text=_('AppUser created the note'),
        related_name='notes',
        on_delete=models.PROTECT
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='notes'
    )

    objects = querysets.NoteQuerySet.as_manager()

    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self):
        return self.title


class VoiceConsent(BaseModel):
    """VoiceConsent.

    Эта модель представляет собой записи о голосовом согласии. Он использовался, когда клиент 
    после этого просмотрел все документы, хочет дать голосовое согласие.

    Атрибуты:
        matter (Matter): Ссылка на вопрос, на который было дано согласие
        title (str): Название голосового согласия
        file (file): Файл голосового согласия
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """

    matter = models.ForeignKey(
        to='Matter',
        on_delete=models.CASCADE,
        related_name='voice_consents'
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
    )
    file = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('File'),
        help_text=_("Voice consent's file")
    )

    objects = querysets.VoiceConsentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Voice Consent')
        verbose_name_plural = _('Voice Consents')
        unique_together = ('matter', 'title')

    def __str__(self):
        return f'Voice Consent ({self.pk}) @ {self.matter}'

    def clean_file(self):
        """ Убедитесь, что этот файл является аудиофайлом. """
        mime_type = mimetypes.guess_type(str(self.file))[0]
        if mime_type not in settings.AUDIO_MIME_TYPES:
            raise ValidationError(
                "Voice consent's file must be an audio file"
            )


class MatterSharedWith(BaseModel):
    """MatterSharedWith.

    Определяет пользователей, которые имеют доступ к не принадлежащим им материалам, и все
    разрешения для этого.

    Бизнес-кейс: адвокат по первоначальному делу может пригласить других пользователей для 
    участия в его деле, чтобы они могли помочь ему (адвокаты или пользователи службы поддержки).

    Атрибуты:
        matter (Matter): Ссылка на дело, которой делятся с адвокатом
        user (AppUser): Ссылка на пользователя, с которым предоставлен общий доступ к материалам
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    matter = models.ForeignKey(
        to='Matter',
        on_delete=models.CASCADE,
        related_name='shared_links',
        verbose_name=_('Matter'),
        help_text=_('Matter that was shared with mediator')
    )
    user = models.ForeignKey(
        to=AppUser,
        on_delete=models.CASCADE,
        related_name='shared_links',
        verbose_name=_('User'),
        help_text=_('User with which matter was shared')
    )

    objects = querysets.MatterSharedWithQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Shared With')
        verbose_name_plural = _('Matters Shared With')
        unique_together = ('matter', 'user')

    def __str__(self):
        return f'Shared with ({self.pk}) @ {self.matter}'


class InvoiceActivity(BaseModel):
    """Invoice Activity

    Эта модель представляет события ("действия"), которые произошли во фрейме
    этого счета-фактуры (например: "Отправлен ежемесячный счет-фактура` и т.д.).

    Атрибуты:
        activity (str): имя/заголовок созданного действия
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    activity = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_('Activity'),
        help_text=_('Title which describes current activity')
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('InvoiceActivity')
        verbose_name_plural = _('InvoiceActivities')

    def __str__(self):
        return self.activity


class InvoiceLog(BaseModel):
    """Invoice Log

    Эта модель представляет события ("журнал"), которые произошли во фрейме
    из этого счета-фактуры (например: `200 POST /v1/incoice/in_1ITVSK34FJV/отправить`
    и т.д.).

    Атрибуты:
        status (str): код ответа stripe API
        method (str): журнал методов stripe API
        log (str): журналы stripe API
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз

    """
    status = models.CharField(
        max_length=20,
        null=True,
        verbose_name=_('Status'),
    )

    method = models.CharField(
        max_length=10,
        null=True,
        verbose_name=_('Method')
    )

    log = models.CharField(
        max_length=255,
        null=True,
        verbose_name=_('Logs'),
        help_text=_('Title which describes current log'),
    )

    objects = querysets.MatterRelatedQuerySet.as_manager()

    class Meta:
        verbose_name = _('InvoiceLog')
        verbose_name_plural = _('InvoiceLogs')

    def __str__(self):
        return self.log
