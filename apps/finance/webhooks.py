"""
Этот модуль хранит обработчики webhook через dj-stripe
Забудьте о пользовательских обработчиках регистраций, нужно поместить их в
импортируемый модуль, как models.py

dj-stripe отвечает за обновление данных о клиентах, подписках,
тарифных планах и т.д
"""
import logging
from django_fsm import TransitionNotAllowed
from djstripe import models, webhooks
from djstripe.event_handlers import _handle_crud_like_event
from djstripe.models import Event

from .models import (
    AccountProxy,
    PaymentIntentProxy,
    PlanProxy,
    SubscriptionProxy,
)
from .services import stripe_deposits_service

logger = logging.getLogger('stripe')


@webhooks.handler("invoice.payment_succeeded")
def handle_subscription_payment_succeeded(event: Event):
    """ Обработчик предоставляет действия для успешного завершения или обновления
    подписки.

    * Продлить подписку пользователя на has_active_subscription
    * Проверьте значение параметра `рекомендуемый` для адвоката
    * Проверьте настройку "период действия промо-акции" для первой подписки

    Raise:
        Определение Plan TypeError, если получено сообщение об ошибке при получении типа плана
    """
    logger.info(event.data)

    user = event.customer.subscriber
    invoice, _ = _handle_crud_like_event(
        target_cls=models.Invoice,
        event=event,
    )
    #subscription = SubscriptionProxy.objects.get(id=invoice.subscription.id)
    #user.active_subscription = subscription
    #user.save()
    # Получить объект счета-фактуры для получения связанного плана
    is_premium = PlanProxy.check_is_premium(invoice.plan)
    if is_premium:
        user.mediator.featured = True
        user.mediator.save()


@webhooks.handler(
    "invoice.payment_action_required",
    "invoice.payment_failed",
    "customer.subscription.deleted"
)
def handle_subscription_payment_failed(event: Event):
    """ Рассматривает дела, в которых адвокату отказано в доступе

    Это происходит, если:
     * Платеж не состоялся
     * Подписка была отменена и завершилась

    Отключите доступ адвоката к платным ресурсам,
    отключите `рекомендуемые` возможности

    """
    logger.info(event.data)

    user = event.customer.subscriber
    if event.type == "customer.subscription.deleted":
        subscription_id = event.data['object']['id']
    else:
        invoice, _ = _handle_crud_like_event(
            target_cls=models.Invoice,
            event=event,
        )
        subscription_id = SubscriptionProxy.objects.get(
            id=invoice.subscription.id
        ).id

    # ничего не делайте, если пользователь больше не существует в базе данных
    if not user:
        return

    # Событие `"customer.subscription.deleted"` запущено для пробной версии в будущем
    # подписки. Если эта отмененная подписка не является актуальной для пользователя
    # - нечего делать

    #if (user.active_subscription and
    #        user.active_subscription.id == subscription_id):
    #    user.active_subscription = None
    #    user.save()
    #if not user.active_subscription:
    #    user.mediator.featured = False
    #    user.mediator.save()


@webhooks.handler("invoice.created")
def handle_adding_promo_period_to_subscription(event: Event):
    """ Мы предоставляем промо-период для первой 18-месячной подписки на эмуляцию

    Добавление периода действия акции реализовано для события "invoice.created", 
    когда создается счет-фактура, создается за час до списания
    средств в день окончания подписки

    Связанные документы:
    https://stripe.com/docs/billing/lifecycle#subscription-lifecycle

    ЗАДАЧА: этот метод должен быть удален после истечения срока действия подписки v1
    """
    logger.info(event.data)

    user = event.customer.subscriber
    invoice, _ = _handle_crud_like_event(
        target_cls=models.Invoice,
        event=event,
    )

    billing_reason = event.data['object']['billing_reason']

    # Когда закончится первый год подписки, установите пробную версию в течение шести месяцев
    if all([
        not user.finance_profile.was_promo_period_provided,
        billing_reason == 'subscription_cycle']
    ):
        SubscriptionProxy.set_promo_period_v1(invoice.subscription)
        user.finance_profile.was_promo_period_provided = True
        user.finance_profile.save()


@webhooks.handler("account.updated")
def handle_account_updates(event: Event):
    """ Обработчик для выполнения некоторых действий по обновлению учетной записи.
    Информация об учетной записи может быть обновлена stripe в зависимости от статуса ее 
    верификации (прошел ли он верификацию и готов ли к начислениям и выплатам или нет).
    Всякий раз, когда появляется новый webhook, метод обновляет соответствующую информацию об 
    учетной записи в БД и отправляет электронные письма об успешной проверке или нет.
    """
    logger.info(event.data)
    account_id = event.data['object']['id']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # сохраните учетную запись и отправьте электронное письмо пользователю о ее статусе
    account, _ = _handle_crud_like_event(target_cls=AccountProxy, event=event)
    account.notify_user()


@webhooks.handler("capability.updated")
def handle_capability_updates(event: Event):
    """ Обработчик для обновления "capabilities" учетной записи при ее обновлении.
    Изменения возможностей отслеживаются отдельно с помощью stripe API "capabilities",
    потому что мы не можем получить эту информацию с помощью простой повторной синхронизации 
    "Учетной записи" (там это не актуально). Существует проблема в том, что stripe не отправляет 
    "окончательное" событие, которое `учетная запись.обновлена` после успешной проверки 
    `individual.id_number`. Таким образом, мы можем знать, что проверка завершена в конце просто
    из события "возможность.обновлено". Но когда мы получим "возможность.обновлено"
    событие, мы не можем просто повторно синхронизировать данные учетной записи и получать 
    обновленную информацию, потому что Учетная запись будет переведена из состояния "pending" в 
    состояние "completed" только через несколько минут после последнего события 
    "capability.updated", "active".
    """
    logger.info(event.data)
    account_id = event.data['object']['account']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # обновите информацию об учетной записи на всякий случай, если она была обновлена
    account = AccountProxy.resync(account_id)
    stripe_deposits_service.update_capability(
        account, event.data['object']['id']
    )
    account.refresh_from_db()
    account.notify_user()


@webhooks.handler(
    "account.external_account.created",
    "account.external_account.deleted",
    "account.external_account.updated",
)
def handle_external_account_updates(event: Event):
    """ Обработчик для выполнения некоторых действий по обновлению внешней учетной записи.
    Информация о внешней учетной записи может быть обновлена пользователем в его учетной записи 
    Express приборная панель. Всякий раз, когда появляются новые веб-ссылки, метод обновляет 
    соответствующие Информация об учетной записи в базе данных.
    """
    logger.info(event.data)
    account_id = event.data['object']['account']
    finance_profile = stripe_deposits_service.get_finance_profile(account_id)
    if not finance_profile:
        return

    # обновите учетную запись `external_accounts` и уведомите пользователя о его статусе
    account = AccountProxy.resync(account_id)
    account.notify_user()


@webhooks.handler(
    'payment_intent.succeeded',
    'payment_intent.canceled',
    'payment_intent.payment_failed',
)
def payment_intent_status_change(event: Event):
    """ Обрабатывать успешную, неудачную или отмененную оплату счета
    Связанные документы:
    https://stripe.com/docs/payments/intents

    """
    logger.info(event.data)

    payment_intent, _ = _handle_crud_like_event(
        target_cls=PaymentIntentProxy,
        event=event,
    )
    # Намерение платежа не привязано к платежу, пропуск
    if not payment_intent.payment:
        return

    transition_map = {
        'payment_intent.succeeded': 'finalize_payment',
        'payment_intent.canceled': 'cancel_payment',
        'payment_intent.payment_failed': 'fail_payment',
    }

    payment = payment_intent.payment
    try:
        getattr(payment, transition_map[event.type])()
        payment.save()
    except TransitionNotAllowed:
        pass
