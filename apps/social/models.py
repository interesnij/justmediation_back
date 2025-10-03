import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill, Transpose

from ..chats.models import AbstractChat
from ..core.models import BaseModel
from .querysets import ChatQuerySet
from ..users.models.users import AppUser


def upload_mediator_post_image_to(instance, filename):
    """Upload mediator post image to this `mediator_post` folder.
    Returns:
        String. Generated path for image.
    """
    return 'public/mediator_post/{folder}/{filename}'.format(
        folder=uuid.uuid4(),
        filename=filename
    )
    
class MediatorPost(BaseModel):
    """Model defines posts made by mediator in social app.

    More advanced version of posts, which can only be created by mediators.

    Attributes:
        author (mediator): author of post
        title (str): Post's title
        image (file): Image of post
        image_thumbnail (file):
            Preview of post's image, generated automatically
        body (str): post content
        body_preview (str): Text preview of post
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time

    """

    author = models.ForeignKey(
        'users.Mediator',
        related_name='posts',
        on_delete=models.PROTECT
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Post title'),
    )

    image = models.CharField(
        max_length=255,
        verbose_name=_('Post Image'),
        help_text=_('Post Image'),
        blank=True,
        null=True,
    )

    image_thumbnail = models.CharField(
        max_length=255,
        verbose_name=_('Post Image'),
        help_text=_('Post Image'),
        blank=True,
        null=True,
    )

    body = RichTextUploadingField(
        config_name='default',
        verbose_name=_('Body'),
        help_text=_('Content of post')
    )

    body_preview = models.TextField(
        max_length=150,
        verbose_name=_('Preview'),
        help_text=_('Text preview of post')
    )

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f'Post ({self.pk}): {self.title[:50]}'


class SingleChatParticipants(BaseModel):
    appuser = models.ForeignKey(
        AppUser,
        related_name='single_chat_participants',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    chat = models.ForeignKey(
        'Chats',
        related_name='single_chat_participants',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name=_('Favorite')
    )


class Chats(AbstractChat):
    """
    Chat between the appUser can be between any kind of app users.
    Attributes:
        chat_channel (str): id of chat in firestore
        participants (AppUsers): two participants of the chat can be two no
                                 more no less
        created (datetime): timestamp when instance was created
        modified (datetime): timestamp when instance was modified last time
        is_group (Boolean): determines if its a group chat or direct(1v1) chat
    """
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        null=True,
        blank=True
    )
    chat_channel = models.UUIDField(
        unique=True,
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
    )

    participants = models.ManyToManyField(
        AppUser,
        verbose_name=_('Participants'),
        related_name='chats',
        related_query_name="%(app_label)s_%(class)ss",
        through='SingleChatParticipants'
    )
    is_group = models.BooleanField(default=False)

    objects = ChatQuerySet.as_manager()

    class Meta:
        verbose_name = _('Chat')
        verbose_name_plural = _('Chats')


class Message(BaseModel):
    """Model containing chat messages"""
    author = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        verbose_name=_('Author'),
        related_name='chat_messages',
    )
    chat = models.ForeignKey(
        'Chats',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_('Message Type')
    )
    timestamp1 = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Timestamp')
    )
    text = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Message Text')
    )


class MessageAttachment(BaseModel):
    """Model for message attachments"""
    message = models.ForeignKey(
        'Message',
        on_delete=models.CASCADE,
        related_name='attachment'
    )
    file = models.CharField(
        max_length=255,
        verbose_name=_('File'),
        blank=True,
        null=True,
        help_text=_('Document file')
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('File Title')
    )

    def save(self,*args,**kwargs):
        #self.file = self.file.replace(".wav", "") + ".wav"
        if not self.title:
            self.title = self.file.split("/")[-1]
            #self.save(update_fields=['title'])
        super(MessageAttachment, self).save(*args,**kwargs)
