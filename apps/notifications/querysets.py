from django.db import models

from apps.users.models import AppUser

__all__ = (
    'NotificationTypeQuerySet',
    'NotificationDispatchQuery',
)


class NotificationTypeQuerySet(models.QuerySet):
    """Queryset class for `NotificationType` model."""

    def user_types(self, user: AppUser):
        """Get notifications available for user"""
        return self.filter(**{f'is_for_{user.user_type}': True})


class NotificationDispatchQuery(models.QuerySet):
    """Queryset class for `NotificationDispatch` model."""

    def get_allowed_to_notify(self):
        """Get dispatches, which settings allows to notify.

        Also annotate notification's settings.

        """
        from .models import NotificationSetting
        settings_qs = NotificationSetting.objects.filter(
            user=models.OuterRef('recipient')
        )
        return self.annotate(
            by_email=models.Subquery(settings_qs.values('by_email')),
            by_push=models.Subquery(settings_qs.values('by_push')),
        ).filter(
            models.Q(by_email=True) | models.Q(by_push=True)
        )

    def get_unread_count(self):
        """Get number of unread notification"""
        from apps.notifications.models import NotificationDispatch
        return self.exclude(status=NotificationDispatch.STATUS_READ).count()
