from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from apps.core.models import BaseModel
from ... import notifications


class VerifiedRegistrationQuerySet(models.QuerySet):
    """Queryset class for `VerifiedRegistration` model."""

    def verified(self):
        """ Получайте только проверенные экземпляры. """
        return self.filter(
            verification_status=VerifiedRegistration.VERIFICATION_APPROVED
        )


class VerifiedRegistration(BaseModel):
    """Абстрактная модель для функциональности проверки `администратора`.

    Модель добавляет поле `verification_status` со связанной с ним бизнес-логикой и
    вспомогательными методами и может использоваться для различных "пользовательских` моделей 
    (адвокатов, Поддержка пользователей и т.д.).

    Он реализует следующий рабочий процесс проверки регистрации:

        1. Всякий раз, когда регистрируется новый пользователь - отмечайте его как `неактивного` 
        и отправляйте специальное "уведомление" для администраторов платформы, чтобы они могли 
        просмотреть нового пользователя. Пользователь не сможет войти в систему до тех пор, пока 
        он не будет подтвержден администраторами платформы.

        2. Когда администратор помечает пользователя как `проверенного` -> `verification_status` 
        пользователя обновляется до "одобрено", пользователь становится активным и может войти 
        в приложение. Также пользователь получает уведомление по электронной почте о том, что он 
        прошел верификацию.

        3. Когда администратор помечает пользователя как `не верифицированного` -> имя пользователя
        `verification_status` обновляется до `denied`, пользователь становится неактивным
        и не могу войти в приложение. Также пользователь получает уведомление по электронной 
        почте о том, что его верификация была отклонена.

    """
    VERIFICATION_NOT_VERIFIED = 'not_verified'
    VERIFICATION_APPROVED = 'approved'
    VERIFICATION_DENIED = 'denied'

    VERIFICATION_STATUSES = (
        (VERIFICATION_NOT_VERIFIED, _('Not verified')),
        (VERIFICATION_APPROVED, _('Approved')),
        (VERIFICATION_DENIED, _('Denied')),
    )

    verification_status = FSMField(
        max_length=20,
        choices=VERIFICATION_STATUSES,
        default=VERIFICATION_NOT_VERIFIED,
        verbose_name=_('Verification_status')
    )

    objects = VerifiedRegistrationQuerySet.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """ Убедитесь, что заданы все необходимые данные. """
        super().__init__(*args, **kwargs)
        assert self._meta.get_field('user')

    @property
    def is_verified(self):
        """ Укажите, проверяется ли экземпляр модели администраторами. """
        return self.verification_status == self.VERIFICATION_APPROVED

    def register_new_user(self):
        self.user.is_active = False
        self.user.save() 
        #notifications.RegisterUserNotification(self.user).send()

    def verify_by_admin(self, **kwargs):
        self.verify(**kwargs)
        self.save() 
        self.post_verify_by_admin_hook(**kwargs)

        notifications.VerificationApprovedEmailNotification(self.user).send() 

    def decline_by_admin(self, **kwargs):
        self.decline()
        self.save()
        self.post_decline_by_admin_hook(**kwargs)
        notifications.VerificationDeclinedEmailNotification(self.user).send()

    @transition(
        field=verification_status,
        source='*',
        target=VERIFICATION_APPROVED,
    )

    def verify(self, **kwargs):
        self.user.is_active = True
        self.user.save()
        notifications.RegisterUserNotification(self.user).send()

        # вызовите специальный хук для обработки логики проверки пользовательского экземпляра
        # Нет необходимости создавать первоначальную подписку
        # После утверждения пользователь должен перейти к процессу адаптации
        # включая создание подписки
        #self.post_verify_hook(**kwargs)

    @transition(
        field=verification_status,
        source='*',
        target=VERIFICATION_DENIED
    )
    def decline(self, **kwargs):
        """ Отклоните проверку экземпляра пользователя.
        * Изменить статус проверки
        * Обновить пользователя `is_active`
        """
        self.user.is_active = False
        self.user.save()

        # вызовите специальный хук для обработки логики проверки пользовательского экземпляра
        # Нет необходимости создавать первоначальную подписку
        # После утверждения пользователь должен перейти к процессу адаптации
        # включая создание подписки
        #self.post_decline_hook(**kwargs)

    # крючки для добавления пользовательской логики во время процесса `проверки`

    def post_verify_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки". """
        pass

    def post_decline_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки". """
        pass

    def post_verify_by_admin_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки". """
        pass

    def post_decline_by_admin_hook(self, **kwargs):
        """ Отдельный хук для добавления пользовательской бизнес-логики "проверки". """
        pass
