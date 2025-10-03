from rest_framework import serializers
from ..apps import HEALTH_CHECKS


class HealthCheckQuery(serializers.Serializer):
    """ Сериализатор для проверки параметров запроса для конечной точки проверки 
    работоспособности. """
    checks = serializers.MultipleChoiceField(
        required=False,
        choices=HEALTH_CHECKS,
    )


class HealthCheckResult(serializers.Serializer):
    """ Сериализатор для одного результата проверки работоспособности """
    status = serializers.CharField()
    description = serializers.CharField()


class HealthCheckResults(serializers.Serializer):
    """ Сериализатор для получения полных результатов проверки работоспособности. """

    def get_fields(self):
        """ Настройте поля для всех шашек. """
        return {
            health_check: HealthCheckResult(label=health_check, required=False)
            for health_check in HEALTH_CHECKS
        }
