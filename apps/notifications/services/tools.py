from django.db.models import OuterRef, Q, QuerySet, Subquery

from ...notifications import models


def get_allowed_to_notify(
    recipients: QuerySet,
    runtime_tag: str
):
    """Get recipients to which settings allows to notify."""
    settings_qs = models.NotificationSetting.objects.filter(
        user=OuterRef('pk')
    )
    recipients = recipients.annotate(
        by_email=Subquery(settings_qs.values('by_email')),
        by_push=Subquery(settings_qs.values('by_push')),
    ).filter(
        Q(by_email=True) | Q(by_push=True)
    )
    if runtime_tag == 'new_message' or runtime_tag == 'new_chat' \
            or runtime_tag == 'new_video_call':
        return recipients.annotate(
            by_chats=Subquery(settings_qs.values('by_chats')),
        ).filter(by_chats=True)
    elif runtime_tag == 'matter_status_update' \
            or runtime_tag == 'new_matter_shared' \
            or runtime_tag == 'new_matter_referred' \
            or runtime_tag == 'new_matter_accepted' \
            or runtime_tag == 'new_referral_declined' \
            or runtime_tag == 'matter_referral_revoked' \
            or runtime_tag == 'document_uploaded_to_matter'\
            or runtime_tag == 'new_billing_item'\
            or runtime_tag == 'new_invoice':
        return recipients.annotate(
            by_matters=Subquery(settings_qs.values('by_matters')),
        ).filter(by_matters=True)
    elif runtime_tag == 'new_post' or runtime_tag == 'new_mediator_post' \
            or runtime_tag == 'new_post_on_topic':
        return recipients.annotate(
            by_forums=Subquery(settings_qs.values('by_forums')),
        ).filter(by_forums=True)
    elif runtime_tag == 'new_opportunites' \
            or runtime_tag == 'new_registered_contact_shared':
        return recipients.annotate(
            by_contacts=Subquery(settings_qs.values('by_contacts')),
        ).filter(by_contacts=True)

    return recipients
