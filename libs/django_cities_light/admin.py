from django.contrib import admin
from cities_light import admin as cities_light_admin
from cities_light import models
from apps.core import admin as core_admin


class CountryAdmin(admin.ModelAdmin):
    """Read only version of admin from cities_light package."""


class RegionAdmin(admin.ModelAdmin):
    """Read only version of admin from cities_light package."""


class CityAdmin(admin.ModelAdmin):
    """Read only version of admin from cities_light package."""


admin.site.unregister(models.Country)
admin.site.unregister(models.Region)
admin.site.unregister(models.City)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.City, CityAdmin)
