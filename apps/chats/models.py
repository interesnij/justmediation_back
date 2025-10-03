import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.models import AppUser
from ..users.models.users import AppUser
from ..core.models import BaseModel


class AbstractChat(BaseModel):
    """Abstract chat model.

    Attributes:
        title (str): Title of chat
        creator (AppUser): Chat creator
        chat_channel (str): id of chat in firestore
        participants (AppUser): Participants of chat

    """

    chat_channel = models.UUIDField(
        unique=True,
        #editable=False,
        default=uuid.uuid4,
        verbose_name=_('Chat channel ID'),
    )

    participants = models.ManyToManyField(
        AppUser,
        verbose_name=_('Participants'),
        related_name='%(class)ss',
        related_query_name="%(app_label)s_%(class)ss",
    )

    is_favorite = models.BooleanField(
        default=False,
        verbose_name=_('Favorite')
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name=_('Archived')
    )

    class Meta:
        abstract = True

    def is_participant(self, user: AppUser) -> bool:
        """Check whether user is a chat participant."""
        return self.participants.filter(id=user.id).exists()
