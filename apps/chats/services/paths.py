from typing import Union


def get_chat_document_path(chat_id: str) -> str:
    """Get chat document path from chats collection in Firestore."""
    return f'chats/{chat_id}'


def get_user_statistics_document(user_id: str) -> str:
    """Get path for user's document."""
    return f'users/{user_id}'


def get_user_statistics_chat_document(
    user_id: Union[str, int], chat_id: str
) -> str:
    """Get chat document path from user statistics collection in Firestore."""
    return f'{get_user_statistics_document(user_id)}/chats/{chat_id}'
