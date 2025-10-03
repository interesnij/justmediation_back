import logging
from typing import List, Type, Union

from libs.firebase import default_firestore_client

from .paths import (
    get_chat_document_path,
    get_user_statistics_chat_document,
    get_user_statistics_document,
)

logger = logging.getLogger('firestore')


def set_up_chat_channel(
    chat_channel: str,
    participants: List[Union[int, Type[int]]],
    lead_id: int = None,
    group_chat_id: int = None,
    direct_chat_id: int = None,
    opportunity_id: int = None,
    chat_id: int = None,
    **kwargs,
):
    """Set up chat_channel in firestore.

    Attributes:
        chat_channel (str) - unique_id of chat
        participants (list[int]) - list of chat participants
        lead_id (int) - lead id in backend db
        group_chat_id (int) - group chat id id in backend db
        kwargs (dict) - data of chat

    """
    chat_data = kwargs
    if lead_id:
        chat_data['lead_id'] = lead_id
    if group_chat_id:
        chat_data['group_chat_id'] = group_chat_id
    if direct_chat_id:
        chat_data['direct_chat_id'] = direct_chat_id
    if chat_id:
        chat_data['chat_id'] = chat_id
    if opportunity_id:
        chat_data['opportunity_id'] = direct_chat_id
    create(
        chat_channel=chat_channel,
        participants=participants,
        **chat_data
    )
    for user_id in participants:
        create_users_statistics(
            chat_channel=chat_channel,
            user_id=user_id,
            participants=participants
        )


def create(chat_channel: str, **kwargs):
    """Create new chat channel with corresponding params in FireStore.

    Attributes:
        chat_channel (str) - unique_id of chat
        kwargs (dict) - data of chat

    As a result there will be created a new `chat_channel` in FireStore, check
    out structure in `docs/firebase.md`.

    """
    default_firestore_client.create_or_update(
        path=get_chat_document_path(chat_channel),
        data=kwargs
    )


def partial_update(chat_channel: str, **kwargs):
    """Perform partial update for chat in firestore

    Attributes:
        chat_channel (str) - unique_id of chat
        kwargs (dict) - data of chat

    """
    default_firestore_client.partial_update(
        path=get_chat_document_path(chat_channel),
        data=kwargs
    )


def create_users_statistics(
    chat_channel: str,
    user_id: Union[str, int],
    participants: List[Union[int, Type[int]]],
):
    """Create user's statistics related to chat in FireStore."""
    data = {
        'count_unread': 0,
        'last_read_post': None,
        'last_chat_message_text': None,
        'last_chat_message_date': None,
        'participants': participants,
    }

    # Set id for user collection
    # Without any field we won't be able to retrieve all user info
    default_firestore_client.create_or_update(
        path=get_user_statistics_document(user_id=user_id),
        data={
            'id': user_id
        }
    )
    # Create/update chat document for user
    default_firestore_client.create_or_update(
        path=get_user_statistics_chat_document(
            user_id=user_id,
            chat_id=chat_channel
        ),
        data=data
    )


def partial_update_users_statistics(chat_channel: str, user_id: int, **kwargs):
    """Perform partial_update for user's statistics related to chat."""
    default_firestore_client.partial_update(
        path=get_user_statistics_chat_document(
            user_id=user_id,
            chat_id=chat_channel
        ),
        data=kwargs
    )


def delete(chat_channel: str) -> None:
    """Delete related chat channel stuff in FireStore.

    Delete chat from FireStore `chats` collection and remove related to chat
    users statistics from `users/{id}/chats/` for instance client and mediator.

    Attributes:
        chat_channel (str) - chat id in FireStore

    """
    # get chat info before deletion (to clean up participants statistics later)
    firebase_chat = default_firestore_client.get(
        path=get_chat_document_path(chat_channel),
    ).to_dict()

    # do nothing if chat is already deleted
    if not firebase_chat:
        return

    # delete original chat in `chats` collection
    default_firestore_client.delete(
        path=get_chat_document_path(chat_channel),
    )

    # delete user stats according to this chat in `users/{id}/chats` collection
    participants = firebase_chat.get('participants', [])
    for user_id in participants:
        delete_user_statistics(chat_channel=chat_channel, user_id=user_id)


def delete_user_statistics(chat_channel: str, user_id: str):
    """Delete user statistics."""
    default_firestore_client.delete(
        path=get_user_statistics_chat_document(
            user_id=user_id,
            chat_id=chat_channel
        )
    )


def process_m2m_changed_event(
    action: str, pk_set: set, chat_channel: str, participants: List[int]
):
    """Process chat's m2m_changed event.

    Arguments:
        chat_channel (str): id of chat in firestore
        participants(List[int]): list of chats participants
        action (str):
            Action of m2m relation change:
            - pre_add - trigger when we are adding new instance to relation,
              before saving changes
            - post_add - trigger when we are adding new instance to relation,
              after saving changes
            - pre_remove - trigger when we are removing instance from relation,
              before saving changes
            - post_remove - trigger when we are removing instance from
              relation, after saving changes
        pk_set: (set[int]):
            Set of primary keys affected by changes. On each action
            (add and remove) there can be different `pk_set`s.
            For example:
                When we are setting relations for first time like this ->
                instance.m2m.set([1, 2, 3]) -> pk_set will be {1, 2, 3}. If we
                call it again like this instance.m2m.set([1, 2, 4]). Then for
                `pre_add` and `post_add` -> ps_set will be {4} and for
                `pre_remove` and `post_remove` ->  ps_set will be {3}

    """
    post_add = 'post_add'
    post_remove = 'post_remove'
    if action not in (post_add, post_remove):
        return

    partial_update(
        chat_channel=chat_channel,
        participants=participants
    )
    for user_id in participants:
        # Skip it if it's a new or deleted participant
        if user_id in pk_set:
            continue
        partial_update_users_statistics(
            user_id=user_id,
            chat_channel=chat_channel,
            participants=participants
        )
    # Process post_add
    if action == post_add:
        process_post_add_event(
            pk_set=pk_set,
            chat_channel=chat_channel,
            participants=participants,
        )
    # Process post_remove
    elif action == post_remove:
        for user_id in pk_set:
            delete_user_statistics(
                chat_channel=chat_channel,
                user_id=user_id,
            )


def process_post_add_event(
    pk_set: set, chat_channel: str, participants: List[int]
):
    """Process chat's `post_add` in m2m_changed event.

    Create chat stats for added participants after relation is saved.

    """
    for user_id in pk_set:
        create_users_statistics(
            chat_channel=chat_channel,
            user_id=user_id,
            participants=participants,
        )


def process_post_remove_event(pk_set: set, chat_channel: str,):
    """Process chat's `post_remove` in m2m_changed event.

    Remove chats stats for removed participants after relation is saved.

    """
    for user_id in pk_set:
        delete_user_statistics(
            chat_channel=chat_channel,
            user_id=user_id,
        )
