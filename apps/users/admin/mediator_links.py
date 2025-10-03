from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ...core.admin import BaseAdmin
from .. import models


class ModelWithTitleAdmin(BaseAdmin):
    """ Общий администратор для модели с названием """
    list_display = ('id', 'title', 'created')
    search_fields = ('title',)
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'title',
            )
        }),
    )


@admin.register(models.Speciality)
class SpecialityAdmin(ModelWithTitleAdmin):
    """Admin panel for speciality"""


@admin.register(models.FeeKind)
class FeeKindAdmin(ModelWithTitleAdmin):
    """Admin panel for fee  kind"""


@admin.register(models.MediatorUniversity)
class MediatorUniversityAdmin(ModelWithTitleAdmin):
    """Admin panel for University"""


@admin.register(models.Jurisdiction)
class JurisdictionAdmin(BaseAdmin):
    """Admin panel for practice jurisdiction"""
    list_display = ('id', 'country', 'state', 'agency', 'number', 'year')
    search_fields = ('agency',)
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'country', 'state', 'agency', 'number', 'year'
            )
        }),
    )


@admin.register(models.FirmLocation)
class FirmLocationAdmin(BaseAdmin):
    """Admin panel for firm location"""
    list_display = ('id', 'country', 'state', 'address', 'city', 'zip_code')
    search_fields = ('address',)
    fieldsets = (
        (_('Main info'), {
            'fields': (
                'address',
            )
        }),
    )


@admin.register(models.AppointmentType)
class AppointmentTypeAdmin(ModelWithTitleAdmin):
    """Admin panel for appointment type"""


@admin.register(models.PaymentType)
class PaymentTypeAdmin(ModelWithTitleAdmin):
    """Admin panel for payment method"""


@admin.register(models.Language)
class LanguageAdmin(ModelWithTitleAdmin):
    """Admin panel for language"""

@admin.register(models.LawFirm)
class LawFirmAdmin(BaseAdmin):
    """Admin panel for Law Firm"""


@admin.register(models.Currencies)
class CurrenciesAdmin(admin.ModelAdmin):
    list_display = ['title',]
    class Meta:
            model = models.Currencies