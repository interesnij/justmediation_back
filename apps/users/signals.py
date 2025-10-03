import os
import typing
from typing import Union
from django.db.models import signals
from django.dispatch import Signal, receiver
from ..business.models import Stage
from ..documents.models import Folder
from ..notifications.models import NotificationSetting
from ..users import models, utils


new_opportunities_for_mediator = Signal(providing_args=('instance',))
new_opportunities_for_mediator.__doc__ = (
    'Signal which indicates that there are new opportunities for mediator'
)
new_registered_contact_shared = Signal(
    providing_args=('instance', 'receiver_pks', )
)

new_registered_contact_shared.__doc__ = (
    'Signal which indicates a new registered '
    'contact(client) has been shared with mediator'
)
new_unregistered_contact_shared = Signal(
    providing_args=('instance', 'receiver_pks', )
)

new_unregistered_contact_shared.__doc__ = (
    'Signal which indicates a new unregistered '
    'contact(invite) has been shared with mediator'
)

mediator_verified = Signal(providing_args=('instance',))
enterprise_verified = Signal(providing_args=('instance',))
mediator_verified.__doc__ = (
    'Signal which indicates that mediator was verified'
)
enterprise_verified.__doc__ = (
    'Signal which indicates that enterprise was verified'
)

new_user_registered = Signal(providing_args=('instance',))
new_user_registered.__doc__ = (
    'Signal which indicates that mediator or enterprise'
    'are registered'
)


@receiver(signals.post_save, sender=models.Mediator)
@receiver(signals.post_save, sender=models.Enterprise)
@receiver(signals.post_save, sender=models.Support)
def new_user_profile_for_verification(
    instance: Union[
        models.Mediator, models.Enterprise, models.Support
    ],
    created,
    **kwargs
):
    """ Уведомить администраторов о том, что новый профиль адвоката/службы поддержки 
    ожидает проверки. Также сделайте учетную запись пользователя неактивной до тех пор, 
    пока администраторы не подтвердят ее.
    """
    if not created:
        return

    instance.register_new_user()
    if isinstance(instance, models.Mediator):
        Stage.create_default_stages(instance)
    if isinstance(instance, models.Mediator) or \
            isinstance(instance, models.Enterprise):
        return
        #new_user_registered.send(
        #    sender=models.AppUser, instance=instance.user
        #)


@receiver(signals.post_save, sender=models.Mediator)
# @receiver(signals.post_save, sender=models.Enterprise)
@receiver(signals.post_save, sender=models.Support)
def new_user_template_folder(
    instance: Union[
        models.Mediator, models.Support
    ],
    created,
    **kwargs
):
    """ Создайте папку для шаблонов для нового зарегистрированного адвоката/службы поддержки. """
    if not created:
        return

    Folder.objects.create(
        title='Personal templates', is_template=True, owner_id=instance.pk
    )


@receiver(signals.post_save, sender=models.Invite)
def send_invitation_mail(instance: models.Invite, created, **kwargs):
    """ Отправьте электронное письмо с приглашением пользователю 
    (если пользователь был приглашен другим пользователем). """
    if not created or instance.type == models.Invite.TYPE_IMPORTED:
        return

    utils.send_invitation(instance)


@receiver(signals.post_save, sender=models.AppUser)
def set_link_to_user_in_invites(instance: models.AppUser, created, **kwargs):
    """ Установите во всех приглашениях ссылку на нового пользователя с тем 
    же адресом электронной почты. """
    if not created:
        return

    models.Invite.objects.without_user().filter(
        email__iexact=instance.email
    ).update(user=instance)


@receiver(signals.post_save, sender=models.Client)
def inform_inviter_about_user(instance: models.Client, created, **kwargs):
    """ Сообщите адвокату, что пользователь зарегистрирован. """
    if not created:
        return

    invites = models.Invite.objects.filter(
        email__iexact=instance.email
    )
    for invite in invites:
        utils.inform_inviter(invite=invite)


@receiver(signals.post_save, sender=models.UserStatistic)
def new_opportunities_statistics(
    instance: models.UserStatistic, created, **kwargs
):
    """ Отправьте сигнал о том, что для адвоката появились новые возможности. """
    is_opportunities_stat = (
        instance.count > 0 and
        instance.tag == models.UserStatistic.TAG_OPPORTUNITIES
    )
    if not created or not is_opportunities_stat:
        return

    new_opportunities_for_mediator.send(
        sender=models.UserStatistic, instance=instance
    )


@receiver(signals.post_save, sender=models.Mediator)
@receiver(signals.post_save, sender=models.Support)
@receiver(signals.post_save, sender=models.Client)
def enable_notifications(
    instance: typing.Union[
        models.Client,
        models.Mediator,
        models.Support
    ],
    created: bool,
    **kwargs
):
    """ Включите все уведомления для нового клиента, адвоката или службы поддержки. """
    if not created:
        return

    user = instance.user
    NotificationSetting.objects.create(
        user=user, by_email=True, by_push=False
    )


@receiver(signals.m2m_changed, sender=models.Client.shared_with.through)
@receiver(signals.m2m_changed, sender=models.Invite.shared_with.through)
def enable_new_contact_notifications(
    instance: typing.Union[
        models.Client.shared_with.through,
        models.Invite.shared_with.through,
    ],
    **kwargs
):
    user = instance.user
    from apps.business.models import Opportunity
    if user is not None:
        Opportunity.objects.bulk_create(
            [
                Opportunity(
                    client=models.Client.objects.get(user_id=user.id),
                    mediator=models.Mediator.objects.get(user_id=mediator_id)
                )
                for mediator_id in kwargs.get('pk_set')
            ]
        )
    if kwargs.get('pk_set'):
        if isinstance(instance, models.Invite):
            new_unregistered_contact_shared.send(
                sender=models.Invite,
                instance=instance,
                receiver_pks=kwargs.get('pk_set')
            )
        else:
            new_registered_contact_shared.send(
                sender=models.Client,
                instance=instance,
                receiver_pks=kwargs.get('pk_set')
            )
