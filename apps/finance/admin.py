""" Переопределены администраторы моделей djstripe.
Во-первых, все модели администратора `djstripe` отключены, потому
что для проекта JLP существует множество избыточных моделей.
"""
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.core.checks import messages
from django.utils.translation import gettext_lazy as _
from djstripe import admin as stripe_admin
from djstripe.enums import AccountType
from stripe import Account
from libs.admin import mixins as lib_mixins
from ..core import admin as core_admin
from . import models

# отмените регистрацию оригинальных моделей djstripe, чтобы вместо них использовать наши 
# пользовательские модели, потому что для нас слишком много моделей djstripe по умолчанию 
# являются избыточными
for model in apps.all_models['djstripe'].values():
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


@admin.register(models.PlanProxy)
class PlanProxyAdmin(core_admin.ReadOnlyMixin, admin.ModelAdmin):
    """ Представление модели "Plan Proxy" в admin.
    Stripe не позволяет обновлять псевдонимы каких-либо других атрибутов планов.
    """
    change_form_template = 'djstripe/admin/change_form.html'
    list_display = (
        'id',
        'nickname',
        'active',
        'product',
        'interval',
        'created'
    )
    list_filter = ('interval', 'active')
    list_select_related = (
        'product',
    )
    search_fields = ('nickname', 'id')
    readonly_fields = ('id', 'created', 'livemode')

    fieldsets = (
        (_('Main info'), {
            'fields': (
                'id',
                'created',
                'nickname',
                'product',
                'currency',
                'amount',
                'interval',
                'interval_count',
                'billing_scheme',
                'trial_period_days',
                'usage_type',
                'active',
                'livemode',
            )
        }),
    )


@admin.register(models.ProductProxy)
class ProductProxyAdmin(core_admin.ReadOnlyMixin, admin.ModelAdmin):
    """ Представление модели "Product Proxy" в admin.
    Stripe не позволяет обновлять какие-либо другие атрибуты продуктов
    помимо имени
    """

    change_form_template = 'djstripe/admin/change_form.html'

    list_display = ('name', 'type', 'active', 'url', 'statement_descriptor')
    list_filter = ('type', 'active', 'shippable')
    search_fields = ('name', 'id')
    readonly_fields = ('id', 'created', 'livemode')

    fieldsets = (
        (_('Main info'), {
            'fields': (
                'id',
                'name',
                'type',
                'description',
                'active',
                'created',
                'livemode',
                'url',
            )
        }),
    )


@admin.register(models.SubscriptionProxy)
class SubscriptionAdmin(
    core_admin.ReadOnlyMixin, stripe_admin.SubscriptionAdmin
):
    """Djstripe `Subscription` model."""
    list_select_related = (
        'customer',
        'customer__subscriber',
    )
    list_filter = (
        'status',
        'cancel_at_period_end'
    )


class IsActiveCustomerFilter(SimpleListFilter):
    """ Является ли профиль клиента активным в stripe или он был удален. """
    title = _('Is active')
    parameter_name = 'active'
    active = 'active'
    deleted = 'deleted'

    def lookups(self, request, model_admin):
        """ Определите доступные значения фильтра ."""
        return (
            (self.active, 'Active'),
            (self.deleted, 'Deleted')
        )

    def queryset(self, request, queryset):
        """ Фильтровать клиентов, если было передано значение фильтра """
        if self.value() is None:
            return queryset
        return queryset.filter(date_purged__isnull=self.value() == self.active)


@admin.register(models.CustomerProxy)
class CustomerAdmin(core_admin.ReadOnlyMixin, stripe_admin.CustomerAdmin):
    """Djstripe `Customer` model."""
    list_select_related = (
        'subscriber',
    )
    autocomplete_list_filter = (
        'subscriber',
    )
    list_filter = (
        IsActiveCustomerFilter,
        stripe_admin.CustomerHasSourceListFilter,
        stripe_admin.CustomerSubscriptionStatusListFilter,
    )


@admin.register(models.AccountProxy)
class AccountAdmin(
    core_admin.ReadOnlyMixin,
    lib_mixins.RelatedObjectActionsMixin,
    lib_mixins.BaseObjectActionsMixin,
    stripe_admin.AccountAdmin
):
    """Djstripe `AccountProxy` model."""
    list_display = (
        'business_url',
        'country',
        'default_currency',
        'is_verified',
    )
    list_filter = ('details_submitted',)
    search_fields = ('settings', 'business_profile')
    related_models = (
        models.PaymentIntentProxy,
    )
    change_actions = [
        'sync_from_stripe',
    ]
    dev_actions = [
        'sync_from_stripe',
    ]

    def has_delete_permission(self, request, obj=None, *args, **kwargs):
        """ Разрешить удаление прокси-объектов учетной записи для непроизводственной среды. """
        if settings.ENVIRONMENT != 'production':
            return True
        return False

    def get_change_actions(self, request, object_id, form_url):
        """ Ограничить действия администратора по изменению.
        Удалите `sync_from_stripe` для не суперпользователей.

        """
        change_actions = super().get_change_actions(
            request, object_id, form_url
        )
        if not request.user.is_superuser:
            return list(filter(
                lambda x: x not in self.dev_actions, change_actions
            ))
        return change_actions

    def sync_from_stripe(self, request, obj: models.AccountProxy):
        """ Синхронизируйте учетную запись. """
        if obj.type == AccountType.standard:
            self.message_user(
                request=request,
                message='Can only sync users accounts',
                level=messages.WARNING
            )
            return
        models.AccountProxy.sync_from_stripe_data(Account.retrieve(obj.id))
        self.message_user(
            request=request,
            message='Synced',
            level=messages.INFO
        )

    sync_from_stripe.label = "Sync"
    sync_from_stripe.short_description = "Sync from stripe"


@admin.register(models.PaymentIntentProxy)
class PaymentIntentAdmin(
    core_admin.ReadOnlyMixin, stripe_admin.PaymentIntentAdmin
):
    """Djstripe `PaymentIntent` model admin panel."""
    list_display = (
        'customer',
        'amount',
        'description',
    )
    search_fields = (
        'customer__id',
        'invoice__id'
    )
    list_select_related = (
        'on_behalf_of',
        'customer',
        'customer__subscriber',
    )


@admin.register(models.Payment)
class PaymentAdmin(core_admin.ReadOnlyAdmin):
    """Admin for `Payment` model."""
    list_display = (
        'id',
        'status',
        'amount',
        'description',
    )
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'id',
                'payer',
                'recipient',
                'amount',
                'application_fee_amount',
                '_payment_object',
                'description',
                'status',
            )
        }),
    )
    list_filter = (
        'status',
    )
    autocomplete_list_filter = (
        'payer',
        'recipient',
    )

    def _payment_object(self, obj: models.Payment):
        """ Верните HTML-ссылку на платежный объект payment. """
        return self._admin_url(obj.payment_content_object)
