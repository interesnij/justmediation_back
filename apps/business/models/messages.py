from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from . import Attachment
from .matter import Matter
from .querysets import MatterCommentQuerySet, MatterPostQuerySet
from ...users.models.users import AppUser


class MatterPost(BaseModel):
    """ MatterPost
    Сообщения - это связь между адвокатом и клиентом, связанная с делом.
    Атрибуты:
        matter (Материя): внешний ключ к модели Matter.
        title (str): название темы
        comment_count (int): Количество тем поста
        last_comment (Masterpost): Ссылка на последнее сообщение в теме
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз
        participants (AppUser): Приглашенные создателем пользователи
        attachments (Attachment): Вложения по теме вопроса
        seen (bool): Был ли прочитан комментарий по вопросу или нет
        seen_by_client (bool): Если комментарий по вопросу был прочитан
            или не клиентом
    """

    matter = models.ForeignKey(
        'Matter',
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
    )
    title = models.CharField(
        _('Title'),
        max_length=255,
        null=True
    )
    comment_count = models.IntegerField(
        _('Comment count'),
        default=0,
    )
    last_comment = models.ForeignKey(
        'MatterComment',
        verbose_name=_('Last Comment'),
        on_delete=models.SET_NULL,
        related_name='last_comment_on_post',
        null=True,
        blank=True,
    )
    participants = models.ManyToManyField(
        to=AppUser,
        verbose_name=_('Participants'),
        related_name='matter_topic',
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='matter_topic'
    )
    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not')
    )
    seen_by_client = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not by client')
    )

    @property
    def unread_comment_count(self):
        return self.comments.filter(seen=False).count()

    @property
    def unread_comment_by_client_count(self):
        return self.comments.filter(seen_by_client=False).count()

    objects = MatterPostQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Message Post')
        verbose_name_plural = _('Matter Message Posts')


class MatterComment(BaseModel):
    """ MatterComment

    Комментарии по вопросам представляют собой сообщения между
    адвокат и клиент на определенной
    должности, связанной с делом.

    Атрибуты:
        post (MatterTopic): ссылка на сообщение, в котором размещен комментарий.
        author (AppUser): ссылка на автора поста.
        text (text): текст предложения
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз
        seen (bool): Был ли прочитан комментарий по вопросу или нет
        seen_by_client (bool): Если комментарий по вопросу был прочитан или не клиентом
    """
    seen = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter comment has been read or not')
    )
    seen_by_client = models.BooleanField(
        default=False,
        verbose_name=_('Seen'),
        help_text=_('If the matter topic has been read or not by client')
    )
    post = models.ForeignKey(
        'MatterPost',
        on_delete=models.CASCADE,
        verbose_name=_('Post'),
        related_name='comments',
    )
    author = models.ForeignKey(
        AppUser,
        on_delete=models.PROTECT,
        verbose_name=_('Author'),
        related_name='matter_comments',
    )
    participants = models.ManyToManyField(
        to=AppUser,
        verbose_name=_('Participants'),
        related_name='matter_comments_pariticipants',
    )
    deleted_participants = models.ManyToManyField(
        to=AppUser,
        verbose_name=_('Deleted Participants'),
        related_name='matter_comments_deleted_pariticipants',
    )
    text = models.TextField(
        _('Text of the post'),
    )
    attachments = models.ManyToManyField(
        to=Attachment,
        verbose_name=_('Attachments'),
        related_name='matter_comments'
    )

    objects = MatterCommentQuerySet.as_manager()

    class Meta:
        verbose_name = _('Matter Message Comment')
        verbose_name_plural = _('Matter Message Comments')

    def clean_author(self):
        """ Убедитесь, что автор связан с актуальными темами. """
        if not Matter.objects.available_for_user(user=self.author).filter(
            topics=self.pk
        ).exists():
            raise ValidationError('Author is not related to matter.')

    @property
    def matter(self):
        """ Получите соответствующий материал из `темы`. """
        return self.post.matter
