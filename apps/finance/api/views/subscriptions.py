from datetime import datetime, timedelta
from rest_framework import generics, response, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
import stripe
from dateutil.relativedelta import relativedelta
from djstripe import models as stripe_models
from djstripe import settings as djstripe_settings
from apps.core.api.views import (
    BaseViewSet,
    ReadOnlyViewSet,
    UserAgentLoggingMixin,
)
from apps.finance.api import serializers
from apps.finance.models import FinanceProfile, PlanProxy, SubscriptionProxy
from apps.finance.notifications import (
    SubscriptionCancelRequestedEmailNotification,
)
from apps.finance.services import stripe_subscriptions_service
from apps.users.api.permissions import IsMediatorFreeAccess
from apps.users.models import AppUser


stripe.api_key = djstripe_settings.STRIPE_SECRET_KEY

__all__ = (
    'AppUserPaymentSubscriptionView',
    'PlanViewSet',
    'CurrentCustomerView',
    'SubscriptionOptions',
)


class AppUserPaymentSubscriptionView(UserAgentLoggingMixin, GenericViewSet):
    """ Просмотр подписок на платежи пользователей.
    Это представление предоставляет интерфейсу методы работы со Stripe, а также
    подготавливает и сохраняет в базе данных платежные подписки для пользователя.
    """
    pagination_class = None
    permission_classes = (AllowAny,)

    @action(methods=['GET'], detail=False, url_path='get-setup-intent')
    def get_setup_intent(self, request):
        """ Подготовьте установочный интернет-ключ `client_secret` для нового клиента.

        Эта конечная точка получает ключ SetupIntent `client_secret` для нового клиента
        от Stripe. Позже он используется интерфейсом для сбора данных карты и
        подготовки пользовательских способов оплаты с помощью Stripe.

        Нам не нужно сохранять намерение установки и его отношение к AppUser
        (Клиент) в БД, потому что намерение установки - это недолговечная сущность, 
        потому что это срок действия может истечь через 24 часа.

        Stripe documentation:
            https://stripe.com/docs/api#setup_intents
        Card saving workflow:
            https://stripe.com/docs/payments/save-and-reuse

        """
        stripe_setup_intent = stripe_models.SetupIntent._api_create()
        serializer = serializers.SetupIntentTokenSerializer(
            stripe_setup_intent
        )
        return response.Response(
            status=status.HTTP_200_OK, data=serializer.data
        )


class PlanViewSet(ReadOnlyViewSet):
    """ Просмотр набора для планов платежей stripe.
    Этот набор представлений возвращает только данные, доступные 
    для планов оплаты проекта JLP (типы подписок).
    """
    base_permission_classes = AllowAny,
    queryset = PlanProxy.objects.active()
    serializer_class = serializers.PlanSerializer

    def get_queryset(self):
        """ Получать планы с указанием типа пользователя """
        qp = self.request.query_params
        user_type = qp.get('type')
        if user_type is None:
            return super().get_queryset()
        plan_list = []
        for obj in AppUser.objects.all():
            if not hasattr(obj, 'finance_profile'):
                continue
            plan = obj.finance_profile.initial_plan
            if plan is None:
                continue
            if obj.user_type == user_type:
                plan_list.append(plan)
        plan_list = list(set(plan_list))
        return plan_list


class CurrentCustomerView(
    UserAgentLoggingMixin,
    generics.RetrieveAPIView,
    generics.UpdateAPIView,
    generics.GenericAPIView
):
    """ Извлеките текущего пользователя Stripe customer. """
    serializer_class = serializers.CurrentCustomerSerializer
    permission_classes = (IsAuthenticated, )

    def get_object(self):
        """ Получите клиента пользователя (профиль stripe). """
        user = self.request.user
        if not user.customer:
            raise NotFound('You are not registered at stripe yet')
        return user.customer


class SubscriptionViewSet(BaseViewSet):
    """ Просмотр для создания подписки на адвоката
    """

    serializer_class = serializers.NewSubscriptionsSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        """ Создать подписку
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        plan_id = data.pop('plan_id', None)
        token = data.pop('token', None)
        try:
            user = request.user
            customer = stripe_subscriptions_service.\
                create_customer_with_attached_card(
                    user=user,
                    payment_method=token
                )

            """ Ничего не делайте, если у пользователя уже есть действительные подписки """
            if customer.has_any_active_subscription():
                return Response(status=status.HTTP_400_BAD_REQUEST, data={
                    "success": False,
                    "detail": "Subscribing failed "
                              "because you already has valid subscription",
                })

            six_months = datetime.now() + relativedelta(months=+6)
            trial_end = (six_months - datetime(1970, 1, 1)) / timedelta(
                seconds=1
            )
            subscription = SubscriptionProxy.create(
                customer_id=customer.id,
                plan_id=plan_id,
                trial_end=round(trial_end)
            )
            #user.active_subscription = subscription
            #user.save()
            plan = PlanProxy.objects.get(id=plan_id)
            FinanceProfile.objects.update_or_create(
                user=user,
                defaults={'initial_plan': plan}
            )
            return Response(status=status.HTTP_200_OK, data={
                "success": True
            })
        except stripe.error.StripeError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e.user_message)
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })


class PaymentMethodViewSet(BaseViewSet):
    """ Представление для создания способа оплаты """

    serializer_class = serializers.PaymentMethodSerializer
    permission_classes = (IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        """ Перечислите способов оплаты """
        try:
            user = request.user
            payment_methods = []
            if user.customer:
                payment_methods = stripe_models.PaymentMethod.objects.filter(
                    customer_id=user.customer.djstripe_id
                )
            page = self.paginate_queryset(queryset=payment_methods)
            data = serializers.CurrentPaymentMethodSerializer(
                instance=payment_methods,
                many=True
            ).data
            if page is not None:
                return self.get_paginated_response(data)
            else:
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": str(e)
            })

    def create(self, request, *args, **kwargs):
        """ Создать источник способа оплаты """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        token = data.pop('token', None)
        default = data.pop('default', False)
        try:
            user = request.user
            stripe_subscriptions_service.\
                create_customer_with_attached_card(
                    user=user, payment_method=token, set_default=default
                )
            FinanceProfile.objects.update_or_create(user=user)
            return Response(status=status.HTTP_200_OK, data={
                "success": True
            })
        except stripe.error.StripeError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e.user_message)
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        token = data.pop('token', None)
        default = data.pop('default', False)
        pk = kwargs.get('pk', None)
        try:
            user = request.user
            payment_method = stripe_models.PaymentMethod.objects.get(
                djstripe_id=pk
            )
            if token:
                payment_method.detach()
            else:
                token = payment_method.id
            stripe_subscriptions_service.\
                create_customer_with_attached_card(
                    user=user, payment_method=token, set_default=default
                )
            FinanceProfile.objects.update_or_create(user=user)
            return Response(status=status.HTTP_200_OK, data={
                "success": True
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "success": False,
                "detail": str(e)
            })

    def destroy(self, request, pk=None):
        try:
            if pk.isdigit():
                payment_method = stripe_models.PaymentMethod.objects.get(
                    djstripe_id=pk
                )
            else:
                payment_method = stripe_models.PaymentMethod.objects.get(
                    id=pk
                )
            payment_method.detach()
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "detail": str(e)
            })
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionOptions(BaseViewSet):
    """ Представление для изменения подписки на адвоката.

    Доступны следующие действия:
        1. Отмена подписки
        2. Повторная активация подписки
        3. Получите предварительный просмотр, переключив план
        4. Переключение плана подписки

    """
    base_filter_backends = None
    pagination_class = None

    serializer_class = serializers.SubscriptionSerializer
    permission_classes = IsAuthenticated, IsMediatorFreeAccess

    serializers_map = {
        'cancel_subscription': None,
        'reactivate_subscription': None,
        'change_subscription': serializers.SubscriptionSwitchSerializer,
        'preview_change_subscription':
            serializers.SubscriptionSwitchSerializer,
    }

    @action(methods=['post'], url_path='cancel', detail=False)
    def cancel_subscription(self, request, *args, **kwargs):
        """ Отменить текущую подписку (активную или завершающуюся)
        Отмена подписки
        Отмените подписку в конце текущего расчетного периода
        (т.е. на тот период времени, за который адвокат уже заплатил)

        Если у адвоката есть следующая подписка - то она будет отменена и удалена

        """
        # cancel_subscription = stripe_subscriptions_service(
        #     request.user
        # ).cancel_current_subscription()
        # result = self.serializer_class(cancel_subscription)
        # return Response(data=result.data, status=status.HTTP_200_OK)

        # customer = request.user.customer
        # if not customer or not customer.has_any_active_subscription():
        #     return Response(status=status.HTTP_400_BAD_REQUEST, data={
        #         'success': False,
        #         'detail': "You don't have active membership now"
        #     })

        email = SubscriptionCancelRequestedEmailNotification(
            user=request.user,
        )
        is_sent = email.send()
        if is_sent:
            return Response(status=status.HTTP_200_OK, data={
                'success': True,
                'detail': 'Your membership cancel request is submitted'
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                'success': False,
                'detail': 'Something went wrong, please contact Administrator'
            })

    @action(methods=['post'], url_path='reactivate', detail=False)
    def reactivate_subscription(self, request, *args, **kwargs):
        """ Повторно активирует отмененную подписку
        Подписка на повторную активацию
        Если подписка адвоката отменена и он еще не достиг
        по окончании расчетного периода он может быть повторно активирован
        """
        reactivate_subscription = stripe_subscriptions_service(
            request.user
        ).reactivate_cancelled_subscription()
        result = self.serializer_class(reactivate_subscription)
        return Response(data=result.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='change/preview', detail=False)
    def preview_change_subscription(self, request, *args, **kwargs):
        """ Вернуть подготовленную информацию о плане переключения
        Подготовьте адвоката для покрытия любых дополнительных расходов, связанных с
        изменением плана или датой продления
        """
        serializer_class = super().get_serializer_class()
        serializer = serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data['plan']
        preview = stripe_subscriptions_service(
            request.user
        ).calc_subscription_changing_cost(new_plan=plan)

        result = serializers.SubscriptionSwitchPreviewSerializer(preview)
        return Response(data=result.data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='change', detail=False)
    def change_subscription(self, request, *args, **kwargs):
        """ Измените план подписки на адвоката
        1. `Понизить подписку`
        Когда план адвоката понижается до "стандартного", они будут
        сохраните их премиум-подписку до следующей даты выставления счета за
        `активные` подписки

        2. `Обновить подписку`
        Когда тарифный план адвоката меняется на `премиум` для `активной` подписки, то:
            * Немедленно переключите свою премиум-подписку
            * Сгенерируйте разовый счет-фактуру для оплаты адвокатом разницы в цене
            при переходе на более дорогой тарифный план

        Для "пробных" подписок не имеет значения, что это за новый план -
        подписки будут изменены немедленно, и никаких новых предстоящих счетов-фактур не будет.
        будет сгенерирован.

        # ЗАДАЧА: Перейти к отдельному API
        Если у адвоката нет активной подписки - создается новая.

        """
        serializer_class = super().get_serializer_class()
        serializer = serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        plan = serializer.validated_data['plan']
        renewed_subscription = stripe_subscriptions_service(
            request.user
        ).change_subscription_plan(new_plan=plan)

        result = serializers.SubscriptionSerializer(
            renewed_subscription
        )
        print("plan", plan);
        print("data", result.data);
        return Response(data=result.data, status=status.HTTP_200_OK)
