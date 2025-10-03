from rest_framework import serializers
from ....core.api.serializers import BaseSerializer
from ... import models


class PaymentObjectDataSerializer(serializers.Serializer):
    """ Сериализатор представляет данные объекта оплаты для модели `Payment`"""

    client_secret = serializers.CharField(allow_null=True)
    status = serializers.CharField()


class PaymentSerializer(BaseSerializer):
    """ Сериализатор для модели `Payment` """

    payment_object_data = PaymentObjectDataSerializer()

    class Meta:
        model = models.Payment
        fields = (
            'id',
            'payer',
            'recipient',
            'amount',
            'application_fee_amount',
            'description',
            'status',
            'payment_object_data',
        )


class StartPaymentParamsSerializer(serializers.Serializer):
    """ Сериализатор для модели поиска в модели информации о платежах. """

    object_type = serializers.ChoiceField(choices=(
        'invoice', 'support'
    ))
    object_id = serializers.IntegerField()
