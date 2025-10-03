from datetime import timedelta

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone

from libs.docusign.constants import ENVELOPE_STATUS_CREATED

from apps.users import models as user_models

__all__ = (
    'EnvelopeQuerySet',
    'ESignProfileQuerySet',
)


class EnvelopeQuerySet(QuerySet):
    """Queryset class for Envelope model."""

    def available_for_user(self, user: user_models.AppUser):
        """Filter available for user instances.

        As far as only mediator can get envelopes - restrict envelopes qs to
        available for him ones.

        """
        return self.filter(matter__mediator__user=user)

    def old_envelopes(self):
        """Filter old envelopes (older then 30 days) depending on env.

        Filter envelopes older than 30 days:

            - with only `created` (`draft`) status - for production env
            - with all statuses - for other envs

        """
        # take 1 day in advance just in case (use 29 instead of 30)
        treshold = timezone.now() - timedelta(days=29)
        envelopes = self.filter(created__lt=treshold)

        if settings.ENVIRONMENT != 'production':
            return envelopes

        return envelopes.filter(status=ENVELOPE_STATUS_CREATED)


class ESignProfileQuerySet(QuerySet):
    """Queryset class for ESignProfile model."""

    def get_profile_by_consent_id(self, consent_id: str):
        """Get only one matching `consent_id` from args in ESignProfile.
        """
        return self.filter(consent_id=consent_id).first()
