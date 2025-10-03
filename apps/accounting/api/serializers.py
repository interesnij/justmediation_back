from rest_framework import serializers
from apps.business.models import Invoice


class AccessAllowedSerializer(serializers.Serializer):
    """Сериализатор для представления успешного обратного вызова auth из Quickbooks.
    Он используется обратным вызовом QB, когда пользователь одобряет запрос на доступ к приложению.
    """
    code = serializers.CharField(required=True)
    realmId = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class AccessDeniedSerializer(serializers.Serializer):
    """Сериализатор для представления обратного вызова проверки подлинности с ошибкой из Quickbooks.
    Он используется обратным вызовом QB, когда пользователь отклоняет запрос на доступ к приложению.
    """
    error = serializers.CharField(required=True)
    state = serializers.CharField(required=True)


class CustomerSerializer(serializers.Serializer):
    """Сериализатор для представления данных клиентов QuickBooks."""
    id = serializers.IntegerField(source='Id')
    display_name = serializers.CharField(source='DisplayName')
    first_name = serializers.CharField(source='GivenName')
    last_name = serializers.CharField(source='FamilyName')
    email = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='CompanyName')

    def get_email(self, obj) -> str:
        """Получите электронное письмо из данных `PrimaryEmailAddr`."""
        email_data = obj['PrimaryEmailAddr']
        return email_data['Address'] if email_data else ''


class ExportInvoiceSerializer(serializers.Serializer):
    """Сериализатор для проверки запроса "Экспорт счета-фактуры"."""
    invoice = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.none(),
        required=True
    )
    customer = serializers.IntegerField(required=False, allow_null=True)

    def __init__(self, qb_api_client=None, *args, **kwargs):
        """Ограничьте количество счетов-фактур, доступных только для пользователей."""
        super().__init__(*args, **kwargs)
        self.qb_api_client = qb_api_client
        request = self.context.get('request')
        if not request or not request.user.is_mediator:
            return
        self.fields['invoice'].queryset = Invoice.objects.all() \
            .available_for_user(request.user)

    def validate_invoice(self, invoice):
        """Подтвердите, что в счете-фактуре указаны временные затраты."""
        if invoice.time_billing.count() == 0:
            raise serializers.ValidationError(
                'Invoice should have time billings'
            )
        return invoice

    def validate_customer(self, customer):
        """Проверьте, существует ли определенный клиент в QuickBooks."""
        if customer:
            customer = self.qb_api_client.get_customer(customer)
        return customer
