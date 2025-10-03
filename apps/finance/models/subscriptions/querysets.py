from django.db import models

__all__ = (
    'PlanProxyQuerySet',
)


class PlanProxyQuerySet(models.QuerySet):
    """Queryset class for `PlanProxySet` model."""

    def active(self):
        """Return available plans for new subscriptions """
        return self.filter(active=True, product__active=True)
