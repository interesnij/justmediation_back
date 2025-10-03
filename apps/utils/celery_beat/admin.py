from django.contrib import admin

from django_celery_beat import admin as celery_beat_admin
from django_celery_beat import models as celery_beat_models

from ...core import admin as core_admin


class DefaultAdmin(core_admin.ReadOnlyMixin, admin.ModelAdmin):
    """Default read only admin."""


class PeriodicTaskAdmin(
    core_admin.ReadOnlyMixin, celery_beat_admin.PeriodicTaskAdmin
):
    """Admin-interface for periodic tasks."""


class ClockedScheduleAdmin(
    core_admin.ReadOnlyMixin, celery_beat_admin.ClockedScheduleAdmin
):
    """Admin-interface for clocked schedules."""


admin.site.unregister(celery_beat_models.IntervalSchedule)
admin.site.unregister(celery_beat_models.CrontabSchedule)
admin.site.unregister(celery_beat_models.SolarSchedule)
admin.site.unregister(celery_beat_models.ClockedSchedule)
admin.site.unregister(celery_beat_models.PeriodicTask)

admin.site.register(celery_beat_models.IntervalSchedule, DefaultAdmin)
admin.site.register(celery_beat_models.CrontabSchedule, DefaultAdmin)
admin.site.register(celery_beat_models.SolarSchedule, DefaultAdmin)
admin.site.register(celery_beat_models.ClockedSchedule, ClockedScheduleAdmin)
admin.site.register(celery_beat_models.PeriodicTask, PeriodicTaskAdmin)
