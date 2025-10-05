from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from constance import config
from libs.notifications.email import DefaultEmailNotification
from libs.utils import get_base_url
from ..finance.notifications import BasePaymentNotification
from ..users import models

# TODO: Улучшите его, когда constance будет поддерживать pytest
# https://github.com/jazzband/django-constance/pull/338

ADMINS_EMAILS = (
    'interesnijsim49293@gmail.com',
    'support@justmediationhub.com',
    'alex.goldobin@justmediationhub.com',
)
MAINTAINERS_EMAILS = config.MAINTAINERS
 

class AdminsEmailNotification(DefaultEmailNotification):
    """ Используется для отправки писем администраторам. """
    recipient_list = ADMINS_EMAILS


class ManagersEmailNotification(DefaultEmailNotification):
    """ Используется для отправки писем менеджерам. """
    recipient_list = MAINTAINERS_EMAILS


class UserEmailNotification(DefaultEmailNotification):
    """ Базовый класс представляет собой интерфейс для отправки электронных 
    писем пользователю. Пользователь экземпляра должен иметь атрибут электронной почты 
    """
    def __init__(self, user):
        super().__init__(recipient_list=(user.email,))
        self.user = user

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'app_user': self.user,
            'user_type': self.user.user_type_display,
            'current_site': get_base_url(),
            'user_key': self.user.uuid,
        }

    def send(self) -> bool:
        self.is_subscribed = self.user.is_subscribed
        super().send()


class VerificationApprovedEmailNotification(UserEmailNotification):
    """ Используется для уведомления адвокатов / пользователей службы поддержки, 
    когда профиль одобрен администратором
    """
    template = 'users/email/verification/email_user_verified.html'

    def get_subject(self):
        """Get email subject."""
        return _('Congratulations! Your application has been approved.')

    def get_template_context(self) -> dict:
        """Add base_url to the context."""
        context = super().get_template_context()
        context['login_url'] = get_base_url()
        return context


class VerificationDeclinedEmailNotification(UserEmailNotification):
    """ Используется для уведомления адвокатов / пользователей службы поддержки, 
    когда администратор отклоняет доступ к профилю.
    """
    template = (
        'users/email/verification/email_user_verification_declined.html'
    )

    def get_subject(self):
        """Get email subject."""
        return _(' Verification Declined')


class RegisterUserNotification(AdminsEmailNotification):
    """ Используется для уведомления администраторов о новых зарегистрированных 
    адвокатах/пользователях службы поддержки. """
    template = ( 
        'users/email/verification/email_new_user_needs_verification.html'
    ) 

    def __init__(self, user):
        super().__init__()
        self.user = user

    def get_subject(self):
        """Get email subject."""
        return _(
            f'New {self.user.user_type_display} is registered'
        )

    def get_template_context(self):
        """Return notification template context."""
        user_type = self.user.user_type
        link_to_admin = reverse_lazy(
            f'admin:users_{user_type}_change',
            # адвокаты и пользователи службы поддержки имеют тот же pk, 
            # что и связанные с ней пользователи
            kwargs={
                'object_id': self.user.pk
            }
        )
        return {
            'app_user': self.user,
            'user_type': self.user.user_type_display,
            'link': f'{settings.BASE_URL}{link_to_admin}'
        }


class InviteNotification(DefaultEmailNotification):
    """ Используется для отправки приглашения клиенту адвоката.  """
    template = 'users/email/invite/email_invitation.html'

    def __init__(self, invite):
        """ Установите экземпляр приглашения и получателя для электронной почты клиента. """
        super().__init__(recipient_list=(invite.email,))
        self.invite = invite

    def get_subject(self):
        return f'You have been invited by {self.invite.inviter}'

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'invite': self.invite,
            'invite_link': self.prepare_invitation_link(),
            'current_site': get_base_url()
        }

    def prepare_invitation_link(self) -> str:
        """ Подготовьте пригласительную ссылку для интерфейсной части. """
        if self.invite.user_type == models.Invite.USER_TYPE_CLIENT or \
                self.invite.user_type == models.Invite.USER_TYPE_LEAD:
            return config.CLIENT_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(), invite=self.invite.uuid
            )
        else:
            return config.MEDIATOR_INVITE_REDIRECT_LINK.format(
                domain=get_base_url(), invite=self.invite.uuid
            )


class RegisteredClientNotification(DefaultEmailNotification):
    """ Используется для отправки электронной почты о зарегистрированном клиенте адвокату. """
    template = 'users/email/invite/email_invited_client_registered.html'

    def __init__(self, invite):
        """ Установите экземпляр приглашения и получателя для электронной почты клиента. """
        super().__init__(recipient_list=(invite.inviter.email,))
        self.invite = invite

    def get_subject(self):
        return f'{self.invite.user.full_name} Has Registered'

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'invite': self.invite,
        }


class BaseFeePaymentNotification(BasePaymentNotification):
    """ Используется для отправки уведомлений о выплатах платы за поддержку. """
    paid_object_name = 'support'

    def get_recipient_list(self):
        """ Электронная почта пользователя службы поддержки. """
        return [self.paid_object.email]

    @property
    def deep_link(self) -> str:
        """ Получите базовую ссылку на интерфейс и перенаправьте 
        пользователя на панель мониторинга. """
        return f'{get_base_url()}'


class FeePaymentSucceededNotification(BaseFeePaymentNotification):
    """ Используется для отправки уведомления о том, что оплата платы за 
    поддержку прошла успешно. """
    template = 'users/email/support/fee_payment_succeeded.html'
    subject = 'Fee Payment for mediator user access paid'


class FeePaymentFailedNotification(BaseFeePaymentNotification):
    """ Используется для отправки уведомления о том, что не удалось оплатить 
    сбор за поддержку. """
    template = 'users/email/support/fee_payment_failed.html'
    subject = 'Fee Payment for mediator user access failed'


class FeePaymentCanceledNotification(BaseFeePaymentNotification):
    """ Используется для отправки уведомления об отмене оплаты комиссии за поддержку. """
    template = 'users/email/support/fee_payment_canceled.html'
    subject = 'Fee Payment for mediator user access canceled'


class EnterpriseMemberInvitationNotification(DefaultEmailNotification):
    """ Используется для отправки приглашений по электронной почте членам enterprise """
    template = 'users/email/invite/email_enterprise_invitation.html'

    def __init__(self, member, enterprise, type):
        """ Укажите экземпляр приглашения и получателя для электронной почты участника. """
        super().__init__(recipient_list=(member.email,))
        self.member = member
        self.enterprise = enterprise
        self.type = type

    def get_subject(self):
        return f'You have been invited to {self.enterprise} team'

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'enterprise': self.enterprise,
            'invite_link': self.prepare_invitation_link()
        }

    def prepare_invitation_link(self) -> str:
        """ Подготовьте пригласительную ссылку для интерфейсной части. """
        return config.MEDIATOR_INVITE_REDIRECT_LINK.format(
            domain=get_base_url(),
            invite=self.enterprise.pk
        )
