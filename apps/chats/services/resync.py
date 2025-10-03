# Приведенный ниже код используется для повторной синхронизации FireBase DB с серверной базой данных. Он удаляет избыточные
# пользователи (которых нет в серверной базе данных) и их чаты. Также обновляет данные
# в существующих чатах.
# Это необходимо для очистки и актуализации firebase DB с помощью backend DB.
import logging
from collections import defaultdict

from google.api_core.exceptions import NotFound
from google.cloud.firestore_v1 import DocumentSnapshot

from libs.firebase import default_firestore_client

from ...business.models import Lead
from ...social.models import Chats
from ...users.models import AppUser
from .chat_channels import (
    delete,
    delete_user_statistics,
    partial_update,
    partial_update_users_statistics,
)

logger = logging.getLogger('firestore')


def sync_chats():
    """Синхронизируйте чаты в firebase.
    Обновите данные графиков и их статистические документы.
    Удалите избыточных пользователей (которых нет в серверной базе данных) и их чаты.
    Также он удаляет все избыточные чаты.
    """
    logger.info('Firebase sync started')
    existing_chat_channels = get_existing_chat_channels()
    logger.info('Updating chats data')
    update_chat_data(existing_chat_channels)
    logger.info('Deleting redundant chats')
    delete_redundant_chats(existing_chat_channels)
    logger.info('Deleting redundant users')
    delete_redundant_users(existing_chat_channels)
    logger.info('Firebase sync finished')


def get_existing_chat_channels() -> dict:
    """Get all existing chat channels and it's participants."""
    leads_data = Lead.objects.all().values(
        'chat_channel', 'mediator', 'client',
    )
    existing_chat_channels = defaultdict(dict, **{
        str(lead_data['chat_channel']): dict(
            participants=[lead_data['mediator'], lead_data['client']],
        )
        for lead_data in leads_data
    })
    group_chats_data = Chats.objects.all().values(
        'chat_channel', 'participants',
    )
    for group_chat_data in group_chats_data:
        group_chat = existing_chat_channels[
            str(group_chat_data['chat_channel'])
        ]
        if 'participants' not in group_chat:
            group_chat['participants'] = []
        group_chat['participants'].append(group_chat_data['participants'])
    return existing_chat_channels


def update_chat_data(existing_chat_channels: dict):
    """Update chat and users chats statistics data."""
    for chat_channel, data in existing_chat_channels.items():
        try:
            partial_update(chat_channel=chat_channel, **data)
            for participant in data['participants']:
                try:
                    partial_update_users_statistics(
                        user_id=participant,
                        chat_channel=chat_channel,
                        participants=data['participants']
                    )
                except NotFound:
                    logger.info(
                        f'Chat stats {chat_channel} '
                        f'for {participant} not found'
                    )
        except NotFound:
            logger.info(f'Chat {chat_channel} not found')


def delete_redundant_chats(existing_chat_channels: dict = None):
    """Delete chats from FireBase that doesn't exist in backend db."""
    chats_collection = default_firestore_client.list('chats', )

    # chat_channels from firebase
    chat_channels = set(chat.id for chat in chats_collection)

    # chat_channels from backend db
    if not existing_chat_channels:
        existing_chat_channels = get_existing_chat_channels()

    existing_chat_channels_ids = set(existing_chat_channels.keys())
    redundant_chat_channels = chat_channels - existing_chat_channels_ids
    for chat_channel in redundant_chat_channels:
        logger.info(f'Deleting chat {chat_channel}')
        delete(chat_channel=chat_channel)


def delete_redundant_users(existing_chat_channels: dict = None):
    """Delete users from FireBase that doesn't exist in backend db."""
    users_collections = default_firestore_client.list('users')

    # user ids from backend db
    existing_users = set(map(
        str, AppUser.objects.all().values_list('id', flat=True)
    ))
    for user_collection in users_collections:
        if user_collection.id in existing_users:
            logger.info(
                f'Deleting redundant chats for user:{user_collection.id}'
            )
            delete_redundant_user_chats(
                user_chats=user_collection,
                user_id=user_collection.id,
                existing_chat_channels=existing_chat_channels
            )
            continue

        logger.info(f'Non existing user found -> user:{user_collection.id}')
        delete_user(user_collection)


def delete_user(user_collection: DocumentSnapshot):
    """Delete user's chats and it's info from firebase."""
    user_id = user_collection.id
    logger.info(f'Deleting user:{user_id} chats')
    # First we need to delete all chats because in firebase you can't delete
    # all collection's documents by one command. If you do this, then user
    # folder become virtual, add all chats won't be deleted and you won't be
    # able to access to this user folder.
    delete_redundant_user_chats(
        user_collection, user_id=user_id, delete_all=True
    )
    logger.info(f'Deleting user:{user_id} document')
    # Deleting user document
    default_firestore_client.delete(user_collection.reference.path)


def delete_redundant_user_chats(
    user_chats: DocumentSnapshot,
    user_id: str,
    existing_chat_channels: dict = None,
    delete_all: bool = False,
):
    """Delete users' chats from FireBase that doesn't exist in db.

    If delete_all is passed delete all of them.

    """

    # chat_channels from backend db
    if not existing_chat_channels:
        existing_chat_channels = get_existing_chat_channels()

    if delete_all:
        redundant_chat_channels = existing_chat_channels
    else:
        # chat_channels from firebase
        chat_path = f'{user_chats.reference.path}/chats'
        chats = default_firestore_client.list(chat_path)
        chat_channels = set(chat.id for chat in chats)
        existing_chat_channels_ids = set(existing_chat_channels.keys())
        redundant_chat_channels = chat_channels - existing_chat_channels_ids

    for chat_channel in redundant_chat_channels:
        logger.info(f"Deleting redundant user's chat {chat_channel}")
        delete_user_statistics(chat_channel=chat_channel, user_id=user_id)
