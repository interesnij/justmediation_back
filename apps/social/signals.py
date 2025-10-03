from django.db.models import signals
from django.dispatch import Signal, receiver

from ..chats.services import chat_channels
from .models import Chats

added_to_group_chat = Signal(providing_args=('instance',))
added_to_group_chat.__doc__ = (
    'Signal that mediators have been invited to group chat'
)

added_to_new_chat = Signal(providing_args=('instance',))
added_to_new_chat.__doc__ = (
    'Signal that mediator have added new participants to a chat'
)

new_chat_message = Signal(providing_args=('instance',))
new_chat_message.__doc__ = (
    'Signal that a new chat message is created'
)


@receiver(signals.post_save, sender=Chats)
def create_single_chat_channel(instance: Chats, created, **kwargs):
    """Set chat channel in FireStore on new new Chat creation.

    When new chat created there should be sent a request to create
    new chat(group chat) with defined required info.
    Participants are set in set_chat_participants signal.

    """
    if not created:
        return

    chat_channels.set_up_chat_channel(
        chat_channel=instance.chat_channel,
        participants=list(instance.participants.values_list('pk', flat=True)),
        chat_id=instance.id,
    )


@receiver(signals.m2m_changed, sender=Chats.participants.through)
def set_single_chat_participants(
    instance: Chats, action: str, pk_set: set, **kwargs
):
    """
        Update participants information in firestore depending on action.
    """
    participants = list(instance.participants.values_list(
        'pk', flat=True
    ))
    chat_channels.process_m2m_changed_event(
        action=action,
        pk_set=pk_set,
        chat_channel=instance.chat_channel,
        participants=participants
    )


@receiver(signals.post_delete, sender=Chats)
def remove_single_chat(instance: Chats, **kwargs):
    """Remove chat channel from Firebase on Chat deletion

    When Chat is deleted there should be sent a request to delete
    corresponding to `chat_channel` chat and user statistics from Firebase.

    """
    chat_channels.delete(chat_channel=instance.chat_channel)
