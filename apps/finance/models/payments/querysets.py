from django.db import models


class AbstractPaidObjectQuerySet(models.QuerySet):
    """Queryset class for `AbstractPaidObject` model."""

    def paid(self):
        """Get paid objects."""
        from .payments import AbstractPaidObject
        return self.filter(
            payment_status=AbstractPaidObject.PAYMENT_STATUS_PAID
        )
