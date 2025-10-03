from abc import ABC, abstractmethod
from typing import List
from libs.notifications import email

__all__ = (
    'StripeAccountNotVerifiedEmailNotification',
    'StripeAccountVerifiedEmailNotification',
    'BasePaymentNotification',
    'StripeAccountVerifiedEmailNotification',
    'StripeAccountNotVerifiedEmailNotification',
)

from libs.notifications.email import DefaultEmailNotification
from libs.utils import get_admin_base_url


class BaseStripeAccountEmailNotification(email.DefaultEmailNotification):
    """ Базовый класс с общей логикой для уведомления учетной записи stripe. """

    def __init__(self, stripe_account_url: str, recipients: List[str]):
        """ Запомните параметры уведомлений.
        Аргументы:
            stripe_account_url (str): url-адрес подключенной учетной записи пользователя в Stripe
            recipients (List[str]): список электронных писем получателей
        """
        super().__init__(recipient_list=recipients)
        self.stripe_account_url = stripe_account_url

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'stripe_account_url': self.stripe_account_url,
        }


class StripeAccountNotVerifiedEmailNotification(
    BaseStripeAccountEmailNotification
):
    """ Отправьте электронное письмо пользователю, если его учетная запись Stripe для прямых 
    депозитов не подтверждена. """

    template = 'finance/email/not_verified_account_notification.html'

    def get_subject(self):
        """Get email subject."""
        return 'Direct deposit account requires extra information'


class StripeAccountVerifiedEmailNotification(
    BaseStripeAccountEmailNotification
):
    """ Отправьте электронное письмо пользователю, когда его учетная запись Stripe для прямых 
    депозитов будет подтверждена. """

    template = 'finance/email/verified_account_notification.html'

    def get_subject(self):
        """Get email subject."""
        return 'Direct deposit account is verified'


class BasePaymentNotification(email.DefaultEmailNotification, ABC):
    """ Используется для отправки уведомлений о платежах пользователя. """
    paid_object_name = None

    def __init__(self, paid_object, **template_context):
        """Init BaseFeePaymentNotification."""
        self.paid_object = paid_object
        super().__init__(
            recipient_list=self.get_recipient_list(),
            **template_context,
        )

    @abstractmethod
    def get_recipient_list(self):
        """ Получите электронное письмо плательщика оплаченного объекта. """

    @abstractmethod
    def deep_link(self) -> str:
        """Get frontend deep link."""

    def get_template_context(self):
        """ Добавьте платный объект, и это глубокая ссылка на контекст электронной почты. """
        context = super().get_template_context()
        context[self.paid_object_name] = self.paid_object
        context['deep_link'] = self.deep_link
        return context


class SubscriptionCancelRequestedEmailNotification(
    DefaultEmailNotification
):
    """ Отправьте электронное письмо администратору, когда пользователь 
    запросит отменить свою подписку. """
    recipient_list = ['support@JustMediation.com']
    template = 'finance/email/subscription_cancel_requested.html'

    def __init__(self, user):
        """ Запомните параметры уведомлений.
        Аргументы:
            user: экземпляр AppUser, запросивший отмену подписки

        """
        super().__init__()
        self.user = user

    def get_template_context(self):
        """ Верните контекст шаблона уведомления. """
        return {
            'firstname': self.user.first_name,
            'lastname': self.user.last_name,
            'email': self.user.email,
            'cancel_admin_link':
                '{0}users/mediator/{1}/actions/cancel_subscription/'.format(
                    get_admin_base_url(),
                    self.user.pk
                ),
        }

    def get_subject(self):
        """Get email subject."""
        return 'Memebership cancel requested'
