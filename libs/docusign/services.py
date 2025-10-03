import logging
from typing import List
from docusign_esign import EnvelopeEvent, EventNotification
from .constants import ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SIGNED


__all__ = (
    'get_envelope_status_notification',
)

logger = logging.getLogger('docusign')


def get_envelope_status_notification(
    statuses: List[str], webhook_url: str
) -> EventNotification:
    """ Генерируйте уведомление из DocuSign об изменении статуса конверта.
    Метод - это ярлык, который генерирует уведомление обо всех статусах
    изменения.

    Не разрешается создавать уведомления о событиях в разделе "создано"
    и статусы `подписано` в DocuSign API.

    Атрибуты:
        statuses (list) - список статусов, для которых выполняется событие
            уведомления должны быть сгенерированы
        webhook_url (str) - url, по которому DocuSign будет создавать webhooks при
        обновлении статуса конверта

    Возвращается:
        Event Notification - настроенный объект уведомления, который будет
            запускать внутренний api при любом изменении статуса конверта.

    """
    track_statuses = set(statuses) - \
        set([ENVELOPE_STATUS_CREATED, ENVELOPE_STATUS_SIGNED])
    return EventNotification(
        logging_enabled=True,
        require_acknowledgment=True,
        include_envelope_void_reason=True,
        url=webhook_url,
        envelope_events=[
            EnvelopeEvent(envelope_event_status_code=status)
            for status in track_statuses
        ]
    )
