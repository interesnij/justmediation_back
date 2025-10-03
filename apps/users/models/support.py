from django.db import models
from django.utils.translation import gettext_lazy as _
#from ...finance.models import AbstractPaidObject, Payment
from .querysets import SupportQuerySet
from .users import AppUserHelperMixin
from .utils.verification import VerifiedRegistration
from ...users.models.users import AppUser


class Support(AppUserHelperMixin, VerifiedRegistration):
    """ Модель определяет информацию о `поддержке` пользователей.
    Пользователи службы поддержки - это своего рода помощники адвоката, такие как:

        - помощник юриста - физические лица, нанятые адвокатом и выполняющие специально 
        делегированную основную юридическую работу, за которую отвечает адвокат. Параюристы 
        выполняют задачи, требующие знаний закона и юридических процедур. Они похожи на п
        омощников адвоката.

        - канцелярские работники - лица, являющиеся помощниками адвоката, которые выполняют
        больше офисной работы и работы с документами, они похожи на секретарей адвокатов.

        - и т.д.

    У такого рода пользователей нет возможности использовать Django Admin, создавать собственные
    темы, участвовать в форуме или лидах и т.д. Единственный доступный функциональность 
    заключается в управлении "общими с ними" вопросами с помощью связанных с ними
    информация и управление их собственными профилями.

    Существующие адвокаты или клиенты не могут стать пользователями "службы поддержки", это
    отдельно зарегистрированный тип пользователя, который платит определенную "плату", чтобы стать
    `поддержка` после подтверждения администратором.

    Атрибуты:
        user (AppUser): Отношение к AppUser
        description (str): Описание роли
        verification_status (str): есть три статуса:
                not_verified - значение по умолчанию при создании
                approved - Одобрено администраторами
                denied - Отклонено администраторами
        payment_status (str): Статус оплаты комиссии. Может быть:
            * not_started - платеж вот-вот начнется или был отменен и
                будет перезапущен.
            * payment_in_progress - выполняется оплата комиссии
            * payment_failed - попытка оплаты комиссии завершилась неудачей
            * paid - Плата уплачена
        payment (Payment): Ссылка на оплату комиссии
        created (datetime): временная метка, когда был создан экземпляр
        modified (datetime): временная метка, когда экземпляр был изменен в последний раз
    """
    DISPLAY_NAME = 'other'

    user = models.OneToOneField(
        AppUser,
        primary_key=True,
        on_delete=models.PROTECT,
        verbose_name=_('User'),
        related_name='support'
    )
    # ЧТО НУЖНО СДЕЛАТЬ: @Kseniya выясните, кто изменяет и устанавливает `описание` - 
    # администратор или поддержка пользователя
    description = models.CharField(
        max_length=128,
        verbose_name=_('Description'),
        help_text=_("User's description (role)")
    )

    objects = SupportQuerySet.as_manager()

    class Meta:
        verbose_name = _('Other')
        verbose_name_plural = _('Other users')

    def can_pay(self, user) -> bool:
        """ Верните `True`, если `пользователь` может оплатить плату за доступ.
        Плата может быть оплачена только самим пользователем и при регистрации в профиле службы 
        поддержки пользователя проверено.
        """
        if not super().can_pay(user):
            return False
        return user.pk == self.pk and self.is_verified

    def _get_or_create_payment(self) -> Payment:
        """ Создайте платеж за вознаграждение. """
        from ..services import get_or_create_support_fee_payment
        return get_or_create_support_fee_payment(support=self)

    def _post_fail_payment_hook(self):
        """ Уведомить пользователя о несостоявшемся платеже. """
        from .. import notifications
        notifications.FeePaymentFailedNotification(paid_object=self).send()

    def _post_cancel_payment_hook(self):
        """ Уведомить пользователя об отмененном платеже. """
        from .. import notifications
        notifications.FeePaymentCanceledNotification(paid_object=self).send()

    def _post_finalize_payment_hook(self):
        """ Уведомлять пользователя об успешной оплате """
        from .. import notifications
        notifications.FeePaymentSucceededNotification(paid_object=self).send()
