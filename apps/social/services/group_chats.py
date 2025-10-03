import os
from typing import Iterable

from constance import config

from ...users.models import AppUser
from .. import models, signals


def add_participants_to_single_group_chat(
    chat: models.Chats,
    participants: Iterable[AppUser],
    inviter: AppUser,
):
    """Add new participants to group chat.

    Args:
        chat (Chat): chat to which we add participants
        participants (List[AppUser]): list of participants to add
        inviter(AppUser): User that invited participants
    """
    participants = set(map(lambda x: x.pk, participants))
    current_participants = set(chat.participants.values_list(
        'pk', flat=True
    ))
    new_participants = participants - current_participants
    chat.participants.add(*new_participants)

    current_site = config.PROD_FRONTEND_LINK

    # Inform new participants
    new_participants.discard(inviter)
    signals.added_to_new_chat.send(
        instance=chat,
        invited=new_participants,
        inviter=inviter,
        current_site=current_site,
        sender=models.Chats
    )
