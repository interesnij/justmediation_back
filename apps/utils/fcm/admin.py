from django.contrib import admin

from fcm_django.admin import DeviceAdmin
from fcm_django.models import FCMDevice

from ...core import admin as core_admin


class FCMDeviceAdmin(core_admin.ReadOnlyMixin, DeviceAdmin):
    """Read only version of admin from fcm package"""


admin.site.unregister(FCMDevice)
admin.site.register(FCMDevice, FCMDeviceAdmin)
