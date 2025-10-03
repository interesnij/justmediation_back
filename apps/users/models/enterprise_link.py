from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from .. import notifications
from . import Enterprise
from .users import AppUser


class Member(BaseModel):
    """ Модель определяет информацию о членах предприятия
    В нем описывается адрес электронной почты участника и его тип
    Примеры:
        test@test.com
        mediator

    Attributes:
        email(str): электронная почта участника
        type(str): тип пользователя участника
    """

    email = models.EmailField(
        unique=True,
        verbose_name=_('Enterprise member email address'),
    )

    class Meta:
        verbose_name = _('Member')
        verbose_name_plural = _('Members')

    def __str__(self):
        return self.email

    def _send_invitation(self, enterprise, type):
        if not AppUser.objects.filter(email__iexact=self.email).exists():
            notifications.EnterpriseMemberInvitationNotification(
                member=self,
                enterprise=enterprise,
                type=type
            ).send()


class EnterpriseMembers(BaseModel):
    """ Модель определяет информацию о членах предприятия
    В нем описывается адрес электронной почты участника и его тип
    Примеры:
        test@test.com
        mediator

    Attributes:
        email(str): электронная почта участника
        type(str): тип пользователя участника
    """

    USER_TYPE_MEDIATOR = 'mediator'
    USER_TYPES = (
        (USER_TYPE_MEDIATOR, _('Mediator')),
    )

    STATE_PENDING = 'pending'
    STATE_ACTIVE = 'active'
    STATES = (
        (STATE_PENDING, _('Pending')),
        (STATE_ACTIVE, _('Active')),
    )

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE)

    invitee = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        AppUser,
        null=True,
        default=None,
        on_delete=models.CASCADE
    )

    type = models.CharField(
        max_length=10,
        default=USER_TYPE_MEDIATOR,
        choices=USER_TYPES,
        verbose_name=_('Type of member')
    )

    state = models.CharField(
        max_length=10,
        default=STATE_PENDING,
        choices=STATES,
        verbose_name=_('State of member')
    )

    def __str__(self):
        return "{}_{}_{}".format(
            self.enterprise.__str__(),
            self.user.__str__(),
            self.invitee.__str__()
        )
