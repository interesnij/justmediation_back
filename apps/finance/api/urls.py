from django.conf.urls import include, url
from rest_framework import routers
from djstripe.settings import DJSTRIPE_WEBHOOK_URL
from . import views

router = routers.SimpleRouter()

router.register(
    r'subscribe',
    views.AppUserPaymentSubscriptionView,
    basename='subscribe'
)

router.register(
    r'subscription',
    views.SubscriptionOptions,
    basename='mediator-subscription'
)

router.register(
    r'payment-method',
    views.PaymentMethodViewSet,
    basename='payment-method'
)

router.register(
    r'plans',
    views.PlanViewSet,
    basename='plans'
)

router.register(
    r'deposits/auth',
    views.AccountAuthViewSet,
    basename='deposits-auth'
)

router.register(
    r'deposits/profiles',
    views.CurrentAccountViewSet,
    basename='current-account'
)

router.register(
    r'payments',
    views.PaymentsViewSet,
    basename='payments'
)

router.register(
    r'subscription',
    views.SubscriptionViewSet,
    basename='subscriptions'
)

urlpatterns = [
    url(r'', include(router.urls)),
    url(
        fr'^stripe/{DJSTRIPE_WEBHOOK_URL}',
        views.ProcessWebhookView.as_view(),
        name='stripe-webhook',
    ),
    url(
        r'^profiles/current/$',
        views.CurrentCustomerView.as_view(),
        name='current-customer'
    )
]
