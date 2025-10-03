import logging
from datetime import datetime
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
import stripe
from djstripe import models as stripe_models
from stripe.error import InvalidRequestError
from apps.core.api.serializers import BaseSerializer
from apps.finance.models import PlanProxy, SubscriptionProxy

__all__ = (
    'SetupIntentTokenSerializer',
    'SubscribeSerializer',
    'ProductSerializer',
    'PlanSerializer',
    'SubscriptionSerializer',
    'CurrentCustomerSerializer',
    'SubscriptionSwitchSerializer',
    'SubscriptionSwitchPreviewSerializer',
)


logger = logging.getLogger('stripe')

class SetupIntentTokenSerializer(serializers.Serializer):
    """ Сериализатор только для чтения для настройки Internet `client_secret`
    Возвращает только `client_secret`, который используется во внешнем 
    интерфейсе перед appuser подписка в stripe.
    """
    client_secret = serializers.ReadOnlyField()


class SubscribeSerializer(serializers.Serializer):
    """ Специальный сериализатор для создания пользовательской подписки
    Атрибуты:
        client_secret (str) - соответствующий SetupIntent секрет клиента
        payment_method (str) - соответствует идентификатору
            SetupIntent payment_method в stripe
        plan (str) - желаемый пользователем идентификатор полосы плана подписки
    """
    client_secret = serializers.CharField(required=True)
    payment_method = serializers.CharField(required=True)
    plan = serializers.CharField(required=True)

    def validate(self, attrs):
        """
        Проверьте правильность данных "Subscriber" для пользователя "client_secret`.
        """
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if not request:
            return attrs

        # проверьте, совпадает ли значение get from frontend setup_intent `client_secret` 
        # с тем же значением как `setup_intent_token`, 
        # сохраненный в кэше для этого пользователя
        cached_token = cache.get(request.user.auth_token.key)
        query_token = attrs['client_secret']
        if cached_token and cached_token['setup_intent_token'] != query_token:
            raise serializers.ValidationError({
                'client_secret': _('Not allowed `client_secret`')
            })
        return attrs


class NewSubscriptionsSerializer(serializers.Serializer):
    """ Сериализатор информации о карте пользователя """
    plan_id = serializers.CharField(required=True)
    token = serializers.CharField(required=True)


class PaymentMethodSerializer(serializers.Serializer):
    """ Сериализатор информации о карте пользователя """
    token = serializers.CharField(required=False)
    default = serializers.BooleanField(required=False)


class ProductSerializer(BaseSerializer):
    """ Сериализатор для модели stripe `Product`. """

    class Meta:
        model = stripe_models.Product
        fields = (
            'id',
            'name',
            'description',
            'type',
            'active',
            'created',
        )


class PlanSerializer(BaseSerializer):
    """ Сериализатор для модели stripe `Plan`. """

    description = serializers.CharField(source='product.description')
    product_data = ProductSerializer(source='product', read_only=True)
    is_premium = serializers.SerializerMethodField()

    class Meta:
        model = stripe_models.Plan
        fields = (
            'id',
            'amount',
            'currency',
            'interval',
            'nickname',
            'description',
            'product',
            'product_data',
            'trial_period_days',
            'is_premium',
        )

    def get_is_premium(self, obj):
        """ Возвращает значение `is_premium` """
        return PlanProxy.check_is_premium(obj)


class SubscriptionSerializer(BaseSerializer):
    """ Сериализатор для модели stripe `SubscriptionProxy`. """

    plan_data = PlanSerializer(
        source='plan',
        read_only=True,
        default=None
    )

    billing_cycle_anchor = serializers.DateTimeField(
        format='%Y-%m-%d',
        read_only=True
    )
    renewal_date = serializers.SerializerMethodField()
    cancel_date = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionProxy
        fields = (
            'id',
            'billing',
            'status',
            'billing_cycle_anchor',
            'canceled_at',
            'cancel_date',
            'renewal_date',
            'cancel_at_period_end',
            'current_period_end',
            'current_period_start',
            'start',
            'plan_data',
            'plan',
            'customer',
            'trial_end',
            'trial_start',
            'metadata',
        )

    def get_cancel_date(self, obj):
        """ Верните `cancel_date`, если подписка была отменена """
        date = SubscriptionProxy.get_cancel_date(obj)
        if date:
            return date.strftime('%Y-%m-%d')

    def get_renewal_date(self, obj):
        """ Верните "renewal_date" зависит от периода действия промо-акции """
        date = SubscriptionProxy.get_renewal_date(obj)
        if date:
            return date.strftime('%Y-%m-%d')


class CurrentCustomerSerializer(BaseSerializer):
    """ Сериализатор для модели djstripe `Customer`. """

    subscription_data = SubscriptionSerializer(
        source='current_subscription', read_only=True
    )
    next_subscription_data = SubscriptionSerializer(
        source='next_subscription', read_only=True
    )

    payment_method = serializers.CharField(
        required=False,
        write_only=True
    )
    payment_method_data = serializers.ReadOnlyField(
        source='default_payment_method.card',
        default=None
    )
    billing_detail_data = serializers.ReadOnlyField(
        source='default_payment_method.billing_details',
        default=None
    )
    name = serializers.ReadOnlyField(
        source='customer.name',
        default=None
    )

    billing_item = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = stripe_models.Customer
        fields = (
            'id',
            'subscription_data',
            'next_subscription_data',
            'payment_method',
            'payment_method_data',
            'billing_detail_data',
            'name',
            'billing_item'
        )
        read_only_fields = fields

    def get_billing_item(self, obj):
        current_invoice = {}
        next_invoice = {}
        if obj.current_subscription:
            result = stripe.Invoice.list(
                subscription=obj.current_subscription.id,
                limit=1
            )
            if result['data'][0].status_transitions.finalized_at:
                current_invoice['date'] = datetime.fromtimestamp(
                    result['data'][0].status_transitions.finalized_at
                ).date().isoformat()
            else:
                current_invoice['date'] = None
            current_invoice['amount'] = result['data'][0].total / 100
            current_invoice['link'] = result['data'][0].invoice_pdf
        if obj.next_subscription:
            result = stripe.Invoice.list(
                subscription=obj.next_subscription.id
            )
            if result['data'][0].status_transitions.finalized_at:
                next_invoice['date'] = datetime.fromtimestamp(
                    result['data'][0].status_transitions.finalized_at
                ).date().isoformat()
            else:
                next_invoice['date'] = None
            next_invoice['amount'] = result['data'][0].total / 100
            next_invoice['link'] = result['data'][0].invoice_pdf
        return {
            "current_invoice": current_invoice,
            "next_invoice": next_invoice
        }

    def save(self, **kwargs):
        """ Выполните обновление `payment_method` по умолчанию для пользователя. """
        payment_method = self.validated_data.get('payment_method')
        if not payment_method or not self.instance:
            return self.instance

        try:
            self.instance.add_payment_method(payment_method)
        except InvalidRequestError as e:
            logger.error(
                f"Couldn't attach new `default_payment_method` "
                f"{payment_method} for customer {self.instance.id}: {e}"
            )
            raise serializers.ValidationError({
                'payment_method': _("Couldn't attach payment method")
            })
        return self.instance


class JSONSerializerField(serializers.Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class CurrentPaymentMethodSerializer(BaseSerializer):
    """ Сериализатор для модели stripe "Способ оплаты". """

    default = serializers.SerializerMethodField(read_only=True)
    card = JSONSerializerField()
    billing_details = JSONSerializerField()

    class Meta:
        model = stripe_models.PaymentMethod
        fields = '__all__'

    def get_default(self, obj):
        if obj.customer is not None and \
                obj.customer.default_payment_method_id == obj.djstripe_id:
            return True
        else:
            return False


class SubscriptionSwitchSerializer(serializers.Serializer):
    """ Короткий сериализатор для получения плана """

    plan = serializers.SlugRelatedField(
        queryset=PlanProxy.objects.filter(active=True),
        slug_field='id'
    )


class SubscriptionSwitchPreviewSerializer(serializers.Serializer):
    """ Сериализатор для представления предварительного просмотра изменения плана """

    new_renewal_date = serializers.DateTimeField(
        format='%Y-%m-%d',
        default=None,
        read_only=True
    )
    cost = serializers.DecimalField(
        allow_null=True,
        required=False,
        decimal_places=2,
        max_digits=20
    )
