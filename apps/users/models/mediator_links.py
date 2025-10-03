import os
import uuid
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.users.validators import validate_activity_year
from .mediators import Mediator


def upload_registration_attachments_to(instance, filename: str) -> str:
    """ Загрузите `documents` адвокатов в папку для регистрации.
        Аргументы:
        instance (Document): доверенность
        filename (str): имя файла documents
        Возвращается:
            str: Сгенерированный путь к файлу documents.
    """
    template = 'public/mediator_registration_attachments/{folder}/{filename}'
    return template.format(
        folder=uuid.uuid4(),
        filename=filename
    )
    
class MediatorEducation(BaseModel):
    """ Определяет отношения "многие ко многим" между адвокатом и университетом.
    Университет - это место, где адвокат изучал юриспруденцию и окончил
    Атрибуты:
        university (University): Университет, в котором адвокат изучал юриспруденцию
        mediator (Mediator): отношение к адвокату
        year (int): Год окончания учебы
    """
    university = models.ForeignKey(
        'MediatorUniversity',
        verbose_name=_('University'),
        related_name='mediator_education',
        on_delete=models.PROTECT
    )
    mediator = models.ForeignKey(
        'Mediator',
        verbose_name=_('Mediator'),
        related_name='education',
        on_delete=models.PROTECT
    )

    year = models.IntegerField(
        verbose_name=_('Year'),
        validators=(
            validate_activity_year,
        )
    )

    class Meta:
        verbose_name = _('Mediator\'s education')
        verbose_name_plural = _('Mediators\' education')


class UniversityQuerySet(QuerySet):
    """QuerySet class `University` model."""

    def verified_universities(self):
        """ Получите все проверенные университеты. Проверенный университет - это университет, 
        в котором учился хотя бы один проверенный адвокат.
        """
        filter_params = {
            'mediator_education__mediator__verification_status':
                Mediator.VERIFICATION_APPROVED
        }
        return self.filter(**filter_params).distinct()


class MediatorUniversity(BaseModel):
    """ Модель определяет университет.
    В нем описывается университет, который закончили адвокаты
    Атрибуты:
        title (str): Название университета
    """

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        unique=True,
    )

    objects = UniversityQuerySet.as_manager()

    class Meta:
        verbose_name = _('Mediator University')
        verbose_name_plural = _('Mediator Universities')

    def __str__(self):
        return self.title


class MediatorRegistrationAttachment(BaseModel):
    """ Файл вложения, добавленный адвокатом при регистрации.
    Атрибуты:
        mediator (Mediator): Ссылка на адвоката
        attachment (file): Добавлено адвокатом при регистрации
    """
    mediator = models.ForeignKey(
        'Mediator',
        verbose_name=_('Mediator'),
        related_name='registration_attachments',
        on_delete=models.CASCADE
    )

    attachment = models.CharField(
        max_length=255,
        verbose_name=_('Attachment file'),
        blank=True,
        null=True,
        help_text=_('Extra file attached by mediator on registration')
    )

    class Meta:
        verbose_name = _("Mediator's registration attachment")
        verbose_name_plural = _("Mediator's registration attachments")

    @property
    def attachment_file_name(self):
        """Get attachment's file name."""
        if self.attachment:
            return os.path.basename(self.attachment)
        return ""
    def __str__(self):
        if self.attachment:
            return (
                f"Mediator {self.mediator.display_name}'s "
                f'attachment: {self.attachment_file_name}'
            )
        return (
                f"Mediator {self.mediator.display_name}'s "
                f'attachment: null'
        )
