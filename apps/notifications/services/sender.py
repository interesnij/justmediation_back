import logging
from django.conf import settings
from fcm_django.models import FCMDevice
from apps.users.models import AppUser
from .email import EmailNotification


logger = logging.getLogger('django')


def send_notification_by_email(
    recipient: AppUser, title: str, content: str, **kwargs
) -> bool:
    """Send notification to recipient by email."""
    logger.info(
        f'Sending email notification: `{title}` to '
        f'{recipient}(pk={recipient.pk})'
    )
    notification = kwargs['notification']
    invoice_sender_email = \
        notification.extra_payload.get('invoice_sender_email', None)
    if invoice_sender_email:
        recipient_list = (invoice_sender_email, )
    else:
        recipient_list = (recipient.email,)
    email_notification = EmailNotification(
        subject=title,
        recipient_list=recipient_list,
        html_message=content
    )
    send_status = email_notification.send()
    if send_status:
        logger.info(
            f'Email notification sent successfully: `{title}` to '
            f'{recipient}(pk={recipient.pk})'
        )
    else:
        logger.error(
            f'Email notification sent failed: `{title}` to '
            f'{recipient}(pk={recipient.pk})'
        )
    return send_status


def send_notification_by_push(
    recipient: AppUser, title: str, content: str, **kwargs
) -> bool:
    """Send notification to recipient by push."""
    logger.info(
        f'Sending push notification: `{title}` to '
        f'{recipient}(pk={recipient.pk})'
    ) 

    # If fcm is disabled just return True
    if not settings.FCM_FIREBASE_ENABLED:
        return True
    recipient_devices = FCMDevice.objects.filter(
        user=recipient,
        active=True
    )
    if not recipient_devices.exists():
        logger.info(f'{recipient} has no devices to push notification')
        return True

    dispatch = kwargs['dispatch']
    notification = kwargs['notification']
    runtime_tag = notification.type.runtime_tag
    if notification.type.runtime_tag == 'new_matter_shared':
        object_id = notification.content_type.model_class().objects.\
            select_related('matter').get(
                pk=notification.object_id
            ).matter.pk
    elif 'proposal' in notification.type.runtime_tag:
        object_id = notification.content_type.model_class().objects.\
            select_related('post').get(
                pk=notification.object_id
            ).post.pk
    elif 'post' in notification.type.runtime_tag and \
            notification.type.runtime_tag != 'new_post_on_topic':
        object_id = notification.content_type.model_class().objects.\
            select_related('post').get(
                pk=notification.object_id
            ).post.pk
    elif notification.type.runtime_tag == 'new_message':
        object_id = notification.content_type.model_class().objects.\
            select_related('post__matter').get(
                pk=notification.object_id
            ).post.matter.pk
    elif notification.type.runtime_tag == 'new_billing_item':
        object_id = notification.content_type.model_class().objects.\
            select_related('matter').get(
                pk=notification.object_id
            ).matter.pk
    elif notification.type.runtime_tag == 'new_invoice':
        object_id = notification.content_type.model_class().objects.\
            select_related('matter').get(
                pk=notification.object_id
            ).matter.pk
    elif notification.type.runtime_tag == \
            'document_uploaded_to_matter':
        object_id = notification.content_type.model_class().objects.\
            select_related('matter').get(
                pk=notification.object_id
            ).matter.pk
    elif notification.type.runtime_tag == \
            'new_chat_message':
        object_id = notification.content_type.model_class().objects.\
            select_related('chat').get(
                pk=notification.object_id
            ).chat.pk
    else:
        object_id = notification.object_id
    notification_data = dict(
        sender_id=dispatch.sender.pk,
        runtime_tag=runtime_tag,
        object_id=object_id,
        dispatch_id=dispatch.pk,
        notification_foreground=True
    )
    notification_data.update(settings.PUSH_NOTIFICATIONS_EXTRA_PARAMS.get(
            runtime_tag, {}
        )
    )
    response = recipient_devices.send_message(
        title=title,
        body=content,
        data=notification_data,
    )

    # Log information about results of the push
    logger.info(format_push_sending_results(response))

    send_status = response['success'] != 0

    if send_status:
        logger.info(
            f'Push notification sent successfully: `{title}` to '
            f'{recipient}(pk={recipient.pk})'
        )
    else:
        logger.warning(
            f'Push notification sent failed: `{title}` to '
            f'{recipient}(pk={recipient.pk})'
        )
    return send_status


def format_push_sending_results(response: dict) -> str:
    """Format fcm response."""
    results = (str(result) for result in response['results'])
    return (
        f"Push notification stats id={response['multicast_ids']}:\n"
        f"Successes: `{response['success']}`\n"
        f"Failures: `{response['failure']}`\n"
        f"Results:\n"
        + '\n'.join(results)
    )
