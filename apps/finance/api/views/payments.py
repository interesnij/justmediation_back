import logging
import typing
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django_fsm import has_transition_perm
from libs.django_fcm.exceptions import TransitionFailedException
from ....business.models import Invoice
from ....core.api.views import BaseViewSet
from ....users.models import Support
from ...models import Payment
from .. import serializers
from ..permissions import IsPaymentPayerPermission


logger = logging.getLogger('django')

class PaymentsViewSet(BaseViewSet):
    """ Представление для управления платежами пользователя. """
    queryset = Payment.objects.all()
    serializer_class = serializers.PaymentSerializer
    serializers_map = {
        'start_payment_process': serializers.StartPaymentParamsSerializer,
        'cancel': None,
    }
    permissions_map = {
        'cancel': (IsPaymentPayerPermission,)
    }

    @action(methods=['post'], detail=False, url_path='start')
    def start_payment_process(self, request):
        """ Запустите процесс оплаты за вводимый объект. """
        input_serializer = self.get_serializer_class()(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        object_to_pay_for = self.get_object_to_pay_for(
            **input_serializer.data
        )

        # Проверьте разрешения
        if not has_transition_perm(
            object_to_pay_for.start_payment_process, self.request.user
        ):
            raise PermissionDenied

        # Начать процесс оплаты
        try:
            payment = object_to_pay_for.start_payment_process(
                user=request.user
            )
        except TransitionFailedException as error:
            logger.error(
                f'Error getting payment for '
                f'`{object_to_pay_for.model_name}` '
                f'#{object_to_pay_for.id}: {error}'
            )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        object_to_pay_for.save()
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(instance=payment).data
        )

    @action(methods=['post'], detail=True)
    def cancel(self, request, *args, **kwargs):
        """ Отменить платеж """
        payment: Payment = self.get_object()

        # Проверьте разрешения
        if not has_transition_perm(
            payment.cancel_payment, request.user
        ):
            raise PermissionDenied
        try:
            payment.cancel_payment()
        except TransitionFailedException as error:
            logger.error(
                f'Error cancelling payment for '
                f'#{payment.id}: {error}'
            )
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        payment.save()
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(instance=payment).data
        )

    def get_object_to_pay_for(
        self, object_type, object_id
    ) -> typing.Union[Invoice, Support]:
        """ Получите объект, который будет оплачен. """
        model_mapping = dict(
            invoice=Invoice,
            support=Support,
        )
        model = model_mapping[object_type]
        return get_object_or_404(
            klass=model,
            pk=object_id,
        )
