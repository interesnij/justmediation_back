from rest_framework import serializers


class TaxRateField(serializers.DecimalField):
    """ Поле, позволяющее использовать пустое значение в сериализаторе. """

    def to_internal_value(self, data):
        """
        Преобразуйте данные в экземпляр `десятичного поля`.
        Если значение пустое, оно преобразуется в ноль.
        """
        if not data:
            return 0
        return super(TaxRateField, self).to_internal_value(data)
