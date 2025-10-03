import re
from django.utils import timezone
from ..users import models, notifications


def send_invitation(invite: models.Invite):
    """ Отправьте клиенту электронное письмо с приглашением. """
    notifications.InviteNotification(invite=invite).send()
    invite.sent = timezone.now()
    invite.save()


def inform_inviter(invite: models.Invite):
    """ Отправьте электронное письмо с приглашением о зарегистрированном клиенте. """
    notifications.RegisteredClientNotification(invite=invite).send()


def format_phone_for_twillio(phone):
    """format phone e.g 1(954) 770-4860 -> +19547704860 """
    if phone:
        phone = re.sub(r'[^\d+]+', '', phone)
        if len(phone) > 1 and phone[0:1] != '+':
            phone = '+' + phone
    return phone
