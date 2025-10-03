from django.db.models import signals
from django.dispatch import Signal, receiver

import django_fsm

from ...chats.services import chat_channels
from ...users.models import AppUser, UserStatistic
from ...users.services import create_stat
from ...users.signals import mediator_verified
from .. import tasks
from ..models import Lead, Matter, Opportunity

__all__ = (
    'matter_status_update',
    'new_lead',
    'matter_status_post_transition',
    'create_shared_folder',
    'add_active_lead_to_stats',
    'add_converted_lead_to_stats',
    'create_chat_channel',
    'remove_chat',
    'send_shared_matter_notification',
    'new_matter_shared',
)

matter_status_update = Signal(providing_args=('instance', 'new_status'))
matter_status_update.__doc__ = (
    'Signal that indicates that status has changed'
)

matter_stage_update = Signal(providing_args=('instance', 'new_status'))
matter_stage_update.__doc__ = (
    'Signal that indicates that status has changed'
)

new_lead = Signal(providing_args=('instance', 'created_by'))
new_lead.__doc__ = (
    'Signal that indicates that there is a new lead created'
)

new_matter = Signal(providing_args=('instance'))
new_matter.__doc__ = (
    'Signal that indicates that there is a new matter created'
)

new_matter_shared = Signal(providing_args=(
    'instance', 'inviter', 'message', 'title'
))
new_matter_shared.__doc__ = (
    'Signal that indicates that matter was shared'
)


@receiver(django_fsm.signals.post_transition, sender=Matter)
def matter_status_post_transition(sender, instance: Matter, field, **kwargs):
    """Send a signal that there is status update for matter."""
    # Check that affected field is 'status' field
    if Matter.status.field == field:
        matter_status_update.send(
            sender=sender,
            instance=instance,
            new_status=instance.status
        )


@receiver(signals.post_save, sender=Matter)
def create_shared_folder(instance: Matter, created: bool, **kwargs):
    """Generate shared folder for Matter."""
    if not created:
        return


@receiver(signals.post_save, sender=Lead)
def add_active_lead_to_stats(instance: Lead, created: bool, **kwargs):
    """Add active lead to stats for mediator and client."""
    if not created:
        return

    if instance.mediator:
        create_stat(
            user=instance.mediator.user, tag=UserStatistic.TAG_ACTIVE_LEAD
        )


@receiver(signals.post_save, sender=Matter)
def add_converted_lead_to_stats(instance: Matter, created: bool, **kwargs):
    """Add converted lead to stats for mediator, if it has one.

    Add converted lead to stats if matter had one.

    """
    lead = instance.lead
    if not created or not lead or lead.is_converted:
        return

    create_stat(
        user=instance.lead.mediator.user, tag=UserStatistic.TAG_CONVERTED_LEAD
    )

    lead.status = Lead.STATUS_CONVERTED
    lead.save()


@receiver(signals.post_save, sender=Lead)
def create_chat_channel(instance: Lead, created, **kwargs):
    """Установите канал чата в Firebase при создании нового клиента.

    При создании нового участника должен быть отправлен запрос на создание нового чата
    с определенным "lead_id" и другой необходимой информацией.
    Также создавайте документы статистики пользователей ведущих участников чата.

    В результате метод устанавливает поле "chat_channel" для созданного интереса.
    """
    if not created:
        return

    # если создан новый клиент - создайте для него чат
    participants_ids = [instance.client_id, instance.mediator_id]
    chat_channels.set_up_chat_channel(
        chat_channel=instance.chat_channel,
        participants=participants_ids,
        lead_id=instance.id,
    )


@receiver(signals.post_save, sender=Opportunity)
def create_opportunity_chat_channel(instance: Opportunity, created, **kwargs):
    """Установите канал чата в Firebase для создания новой ВОЗМОЖНОСТИ.

    При создании новой возможности должен быть отправлен запрос на
    создание нового чата с определенным "opportunity_id" и другой необходимой информацией.
    Также создавайте документы статистики пользователей ведущих участников чата.

    В результате метод устанавливает поле `chat_channel` для созданной возможности.
    """
    if not created:
        return

    # if new Lead is created - create a chat for it
    participants_ids = [instance.client_id, instance.mediator_id]
    chat_channels.set_up_chat_channel(
        chat_channel=instance.chat_channel,
        participants=participants_ids,
        lead_id=instance.id,
    )


@receiver(signals.post_delete, sender=Opportunity)
def remove_opportunity_chat(instance: Opportunity, **kwargs):
    """Remove chat channel from Firebase on Opportunity deletion

    When Opportunity is deleted there should be sent a request to delete
    corresponding to `chat_channel` chat and user statistics from Firebase.

    """
    chat_channels.delete(chat_channel=instance.chat_channel)


@receiver(signals.post_delete, sender=Lead)
def remove_chat(instance: Lead, **kwargs):
    """Remove chat channel from Firebase on Lead deletion

    When Lead is deleted there should be sent a request to delete
    corresponding to `chat_channel` chat and user statistics from Firebase.

    """
    chat_channels.delete(chat_channel=instance.chat_channel)


@receiver(mediator_verified, sender=AppUser)
def send_shared_matter_notification(instance: AppUser, **kwargs):
    """Send `matter shared` notification when user is registered and verified.

    When user with which matter was shared is registered and verified - send
    matter shared notification to him.

    """
    tasks.send_shared_matter_notification_task(instance.id)
