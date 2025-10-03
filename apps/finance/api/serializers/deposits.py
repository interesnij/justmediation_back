from typing import Union
from rest_framework import serializers
from djstripe.models import BankAccount, Card
from drf_yasg.utils import swagger_serializer_method
from ...models import AccountProxy


class SuccessCallbackSerializer(serializers.Serializer):
    """ Сериализатор для представления успешного обратного вызова аутентификации 
    из Stripe connect. """
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class ErrorCallbackSerializer(serializers.Serializer):
    """ Сериализатор для представления обратного вызова авторизации с ошибкой 
    из Stripe connect."""
    error = serializers.CharField(required=True)
    error_description = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class BankAccountSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели djstripe "Bank Account" (только для спецификации swagger).
    Этот сериализатор используется для представления Account `external_accounts`.
    """

    class Meta:
        model = BankAccount
        fields = '__all__'


class CardSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели djstripe `Card` (только для спецификации swagger).
    Этот сериализатор используется для представления учетной записи `external_accounts`.
    """

    class Meta:
        model = Card
        fields = '__all__'


class AccountProxySerializer(serializers.ModelSerializer):
    """ Сериализатор для модели `AccountProxy` """

    capabilities = serializers.JSONField(
        source='info.capabilities',
        read_only=True
    )
    # разделите исходную модель `external_accounts` на 2 поля
    bank_external_account = serializers.SerializerMethodField()
    card_external_account = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = AccountProxy
        fields = (
            'id',
            'charges_enabled',
            'payouts_enabled',
            'requirements',
            'capabilities',
            'bank_external_account',
            'card_external_account',
            'is_verified',
        )

    @swagger_serializer_method(serializer_or_field=BankAccountSerializer)
    def get_bank_external_account(self, obj):
        """ Ярлык для фильтрации только внешнего счета `банк`. """
        return self._filter_accounts_by_type('bank_account', obj)

    @swagger_serializer_method(serializer_or_field=CardSerializer)
    def get_card_external_account(self, obj):
        """ Ярлык для фильтрации только внешней учетной записи `карта`. """
        return self._filter_accounts_by_type('card', obj)

    def _filter_accounts_by_type(
        self, obj_type: str, obj
    ) -> Union[dict, None]:
        """ Ярлык для получения первой доступной учетной записи с помощью `obj_type`.
        Фильтруйте только "первую" учетную запись, потому что панель управления 
        экспресс-учетными записями позволяет добавить только одну учетную запись.
        """ 
        if not hasattr(obj, 'info'):
            return
        accounts = obj.info.external_accounts.get('data', [])
        accounts = list(filter(lambda x: x['object'] == obj_type, accounts))
        return accounts[0] if accounts else None
