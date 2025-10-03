import logging
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from ...models import WebhookEventTriggerProxy

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ProcessWebhookView(View):
    """ Почти оригинальный вид обработчика веб-хуков "dj stripe".

    Единственное отличие заключается в том, что текущее переопределенное представление 
    работает с
    Прокси-модель триггера события Webhook вместо исходного триггера события Webhook. Это
    необходимо, чтобы разрешить использование отдельного секрета webhook для Stripe Connect
    веб-крючки. Итак, теперь simple webhooks используют `DJ STRIPE_WEBHOOK_SECRET` для
    проверки (рабочий процесс подписки), а connect webhooks использует
    `DJSTRIPE_CONNECT_WEBHOOK_SECRET` (рабочий процесс прямого внесения депозитов).

    """

    def post(self, request):
        if "HTTP_STRIPE_SIGNATURE" not in request.META:
            # Даже не пытайтесь обработать /сохранить событие, если
            # в заголовках нет подписи, поэтому мы избегаем переполнения базы данных.
            return HttpResponseBadRequest()

        # единственная разница заключается вот в чем
        trigger = WebhookEventTriggerProxy.from_request(request)

        if trigger.is_test_event:
            # Поскольку мы не проводим проверку подписи, мы должны пропустить
            # trigger.valid
            return HttpResponse("Test webhook successfully received!")

        if not trigger.valid:
            # Событие Webhook не подтвердилось, возвращает 400
            return HttpResponseBadRequest()

        return HttpResponse(str(trigger.id))
