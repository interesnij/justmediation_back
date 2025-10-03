import logging
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
import stripe
from django_fsm import TransitionNotAllowed
from libs.django_fcm.exceptions import TransitionFailedException
from ....core.api import views
from ... import models
from ...models import Invoice, Matter
from ...services import clone_invoice
from .. import filters, pagination, permissions, serializers
from ..serializers.invoices import TimeEntrySerializer
from .core import BusinessViewSetMixin

logger = logging.getLogger('django')


class BillingItemViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """CRUD наборы представлений api для модели BillingItem. """
    queryset = models.BillingItem.objects.select_related(
        'client',
        'client__user',
        'matter',
        'created_by',
        'billed_by',
        'currency',
    ).prefetch_related(
        'invoices',
        'attachments',
        'time_entries',
        'billing_items_invoices',
    )
    pagination_class = pagination.BillingItemLimitOffsetPagination
    serializer_class = serializers.BillingItemSerializer
    serializers_map = {
        'update': serializers.UpdateBillingItemSerializer,
        'partial_update': serializers.UpdateBillingItemSerializer,
    }
    can_edit_permissions = (
        BusinessViewSetMixin.mediator_support_permissions,
        permissions.CanEditOrDeleteInvoiceOrBillingItem,
    )
    permissions_map = {
        'create': (BusinessViewSetMixin.support_permissions,),
        'update': can_edit_permissions,
        'partial_update': can_edit_permissions,
        'destroy': can_edit_permissions,
    }
    filterset_class = filters.BillingItemFilter
    search_fields = (
        'description',
        'matter__title',
        'matter__code',
        'invoices__title'
    )
    ordering_fields = (
        'id',
        'date',
        'created',
        'modified',
        'description',
        'matter__title',
        'client___user__first_name',
        'billed_by__first_name'
    )

    def get_queryset(self):
        qs = super().get_queryset().filter(
            Q(billed_by=self.request.user) |
            Q(created_by=self.request.user) |
            Q(matter__shared_with__in=[self.request.user]) |
            Q(matter__mediator__user=self.request.user)
        ).filter(
            matter__status=Matter.STATUS_OPEN
        ).distinct()
        empty_billing_ids = [
            obj.pk for obj in qs if obj.billing_items_invoices.count() == 0
        ]
        qs = qs.filter(pk__in=empty_billing_ids)
        return qs

    @action(methods=['POST'], detail=False)
    def start_timer(self, request, *args, **kwargs):
        """Запускает таймер для вошедшего в систему пользователя."""

        # Проверьте, запущен ли таймер уже для текущего пользователя
        # # Создайте новую запись времени, если она еще не запущена
        # else возвращает прошедшее время
        billing_item_id = request.data.get('billing_item', None)
        if billing_item_id:
            billing_item = models.BillingItem.objects.get(pk=billing_item_id)
        else:
            billing_item = None

        # Проверьте, существует ли незавершенное отслеживание
        if billing_item:
            if models.TimeEntry.get_running_time_entry(
                request.user,
                None
            ):
                return Response(
                    {"error": "Timer needs to be stopped before starting."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if models.TimeEntry.objects.filter(
                created_by=request.user,
                end_time__isnull=True,
                billing_item__isnull=False,
            ).filter(
                ~Q(billing_item=billing_item)
            ):
                return Response(
                    {
                        "error": "Timer for all billing items needs to be "
                                 "stopped before starting."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if models.TimeEntry.objects.filter(
                created_by=request.user,
                end_time__isnull=True,
                billing_item__isnull=False
            ):
                return Response(
                    {
                        "error": "Timer for all billing items needs to be "
                                 "stopped before starting."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not models.TimeEntry.get_running_time_entry(
            request.user,
            billing_item
        ):
            if billing_item:
                time_entry = TimeEntrySerializer(
                    data={
                        'created_by': request.user.id,
                        'start_time': timezone.now(),
                        'billing_item': billing_item_id
                    }
                )
            else:
                time_entry = TimeEntrySerializer(
                    data={
                        'created_by': request.user.id,
                        'start_time': timezone.now()
                    }
                )
            time_entry.is_valid(raise_exception=True)
            time_entry.save()

            # Сброс предыдущего отслеживаемого времени после начала отслеживания платежного элемента
            if billing_item:
                models.TimeEntry.objects.filter(
                    created_by=request.user,
                    billing_item__isnull=True
                ).delete()

        elapsed_time, _ = models.TimeEntry.elapsed_time_without_microseconds(
            request.user,
            billing_item
        )

        return Response(
            {
                'elapsed_time': elapsed_time
            },
            status=status.HTTP_201_CREATED
        )

    @action(methods=['POST'], detail=False)
    def stop_timer(self, request, *args, **kwargs):
        """ Останавливает таймер для вошедшего в систему пользователя. """
        billing_item = request.data.get('billing_item', None)
        if billing_item:
            billing_item = models.BillingItem.objects.get(pk=billing_item)

        time_entry = models.TimeEntry.get_running_time_entry(
            request.user,
            billing_item
        )
        if time_entry is None:
            return Response(
                {
                    "error": "Timer needs to be started {} before stopping.".
                    format('for that billing item' if billing_item else '')
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        time_entry.end_time = timezone.now()
        time_entry.save()
        elapsed_time, _ = models.TimeEntry.elapsed_time_without_microseconds(
            request.user,
            billing_item
        )

        # Обновить time_spent объекта billing_item
        # после завершения отслеживания платежного элемента
        if billing_item:
            billing_item.time_spent = elapsed_time
            billing_item.save()

        return Response(
            {
                'elapsed_time': elapsed_time
            },
            status=status.HTTP_202_ACCEPTED
        )

    @action(methods=['POST'], detail=False)
    def cancel_timer(self, request, *args, **kwargs):
        """ Отменить таймер для вошедшего в систему пользователя. """
        user = request.user
        models.TimeEntry.objects.filter(created_by=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['GET'], detail=False)
    def get_current_elapsed_time(self, request, *args, **kwargs):
        """ Возвращает время, прошедшее на данный момент. """
        billing_item = request.query_params.get('billing_item', None)
        if billing_item:
            billing_item = models.BillingItem.objects.get(pk=billing_item)
        elapsed_time, is_running = (
            models.TimeEntry.elapsed_time_without_microseconds(
                request.user,
                billing_item
            )
        )

        return Response(
            {
                'elapsed_time': elapsed_time,
                'status': 'running' if is_running else 'stopped'
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['GET'], detail=False)
    def get_running_timer(self, request, *args, **kwargs):
        """ Возвращает запущенный таймер в данный момент. """
        time_entry = models.TimeEntry.objects.filter(
            created_by=request.user,
            end_time__isnull=True
        ).order_by(
            '-created'
        ).first()

        if not time_entry:
            return Response(
                {
                    'message': 'No running timer'
                },
                status=status.HTTP_204_NO_CONTENT
            )

        elapsed_time, is_running = (
            models.TimeEntry.elapsed_time_without_microseconds(
                request.user,
                time_entry.billing_item
            )
        )

        return Response(
            {
                'billing_item': time_entry.billing_item.pk
                if time_entry.billing_item else None,
                'elapsed_time': elapsed_time,
                'status': 'running' if is_running else 'stopped'
            },
            status=status.HTTP_200_OK
        )


class InvoiceViewSet(BusinessViewSetMixin, views.CRUDViewSet):
    """ Набор представлений API для модели Invoice. """
    queryset = models.Invoice.objects.all().select_related(
        'created_by',
        'matter',
        'client__user',
        'matter__mediator',
        'matter__mediator__user',
        'matter__mediator__user__finance_profile',
        'matter__mediator__user__finance_profile__deposit_account',
        'matter__mediator__user__finance_profile__deposit_account__info',
    ).prefetch_related(
        'payment_method',
        'time_billing',
        'billing_items',
        'billing_items__billed_by',
        'activities',
        'logs',
    ).with_fees_earned().with_time_billed()

    can_edit_permissions = (
        BusinessViewSetMixin.mediator_support_permissions,
        permissions.CanEditOrDeleteInvoiceOrBillingItem,
    )

    permissions_map = {
        'create': (BusinessViewSetMixin.support_permissions,),
        'update': can_edit_permissions,
        'partial_update': can_edit_permissions,
        'destroy': can_edit_permissions,
    }

    serializer_class = serializers.InvoiceSerializer
    transition_result_serializer_class = serializers.InvoiceSerializer
    serializers_map = {
        'export': None,
        'draft': serializers.InvoiceSerializer,
        'send': None,
    }
    filterset_class = filters.InvoiceFilter
    search_fields = (
        'title',
        'matter__title',
        'matter__code',
        'matter__client__user__first_name',
        'matter__client__user__first_name',
        'matter__client__organization_name',
    )
    ordering_fields = (
        'id',
        'title',
        'number',
        'created',
        'modified',
        'due_date',
        'matter__title',
        'matter__client__organization_name',
    )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if request.user.is_client:
            qs = qs.filter(~Q(status=Invoice.INVOICE_STATUS_DRAFT))
        queryset = self.filter_queryset(qs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        fields = request.query_params.getlist('ordering', [])
        for field in fields:
            if 'total_amount' in field:
                reverse = False
                if field.startswith('-'):
                    reverse = True
                    field = field[1:]
                data = sorted(
                    data,
                    key=lambda k: (k[field] is not None, k[field]),
                    reverse=reverse
                )
        if page is not None:
            return self.get_paginated_response(data)
        else:
            return Response(data)

    def create(self, request, *args, **kwargs):
        try:
            serializer = serializers.InvoiceSerializer(
                data=request.data, context=super().get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            headers = self.get_success_headers(data)
            invoice = serializer.save()
            invoice.send()
            invoice.save()
            serializer = serializers.InvoiceSerializer(
                instance=invoice
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except TransitionFailedException as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': 'Can not send invoice, please try again after '
                              'verifying all required forms in '
                              'your bank account',
                    'exception': str(e)
                }
            )

    @action(methods=['GET'], detail=True)
    def export(self, request, *args, **kwargs):
        """Экспортируйте счет-фактуру в формате PDF.
        Возвращать:
            ответ(HttpResponse) - ответ с вложением
        """
        obj = self.get_object()
        try:
            return Response(
                data={
                    "link": stripe.Invoice.retrieve(obj.invoice_id).invoice_pdf
                },
                status=status.HTTP_200_OK
            )
        except stripe.error.StripeError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['POST'], detail=True)
    def open(self, *args, **kwargs):
        """ Отправьте клиенту счет по электронной почте. """
        try:
            invoice = self.get_object()
            if models.Invoice.objects.exclude(
                Q(id=invoice.pk) |
                Q(status=models.Invoice.INVOICE_STATUS_DRAFT)
            ).filter(
                billing_items__in=invoice.billing_items.all()
            ).count() > 0:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"detail": (
                        'One or more of these billing '
                        'items has been previously invoiced'
                    )}
                )
            invoice.send()
            invoice.due_date = date.today() + timedelta(days=invoice.due_days)
            invoice.save()
            return Response(
                status=status.HTTP_200_OK,
            )
        except TransitionFailedException as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'detail': 'Can not send invoice, please try again after '
                              'verifying all required forms in '
                              'your bank account',
                    'exception': str(e)
                }
            )
        except TransitionNotAllowed as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)}
            )

    @action(methods=['POST'], detail=True)
    def duplicate(self, request, *args, **kwargs):
        invoice = self.get_object()
        duplicated_invoice = clone_invoice(invoice)
        duplicated_invoice.status = models.Invoice.INVOICE_STATUS_DRAFT
        duplicated_invoice.save()
        serializer = serializers.InvoiceSerializer(
            instance=duplicated_invoice
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(methods=['POST'], detail=False)
    def draft(self, request, *args, **kwargs):
        """ Проект счета-фактуры. """
        serializer = serializers.InvoiceSerializer(
            data=request.data, context=super().get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        headers = self.get_success_headers(data)
        invoice = serializer.save()
        serializer = serializers.InvoiceSerializer(
            instance=invoice
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(methods=['POST'], detail=True)
    def pay(self, request, *args, **kwargs):
        """ Оплатите счет. """
        invoice = self.get_object()
        try:
            invoice.pay()
            invoice.save()
            return Response(
                data=serializers.InvoiceSerializer(invoice).data,
                status=status.HTTP_200_OK,
            )
        except TransitionNotAllowed as e:
            return Response(
                data={'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except TransitionFailedException as e:
            return Response(
                data={'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
