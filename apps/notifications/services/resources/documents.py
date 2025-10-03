from django.db.models import QuerySet

from ....core.models import BaseModel
from ....documents import models as documents_models
from ....documents import signals as documents_signals
from ....users import models as user_models
from ... import models
from .base import BaseNotificationResource


class DocumentSharedNotificationResource(BaseNotificationResource):
    """Notification class for shared files by mediator.

    This notification is sent to client when mediator uploads file to shared
    folder.

    Recipients: Only client

    In designs it's `File Shared` notification type of group 'Matters'.

    """
    signal = documents_signals.document_shared_by_mediator
    instance_type = documents_models.Document
    runtime_tag = 'document_shared_by_mediator'
    title = 'File shared'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'matter_id'
    web_content_template = (
        'notifications/documents/document_shared/web.txt'
    )
    push_content_template = (
        'notifications/documents/document_shared/push.txt'
    )
    email_subject_template = (
        '{{instance.matter.title}} has had a file added to '
        'the shared folder'
    )
    email_content_template = (
        'notifications/documents/document_shared/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.matter.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get client's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.matter.client.pk
        )


class DocumentUploadedNotificationResource(BaseNotificationResource):
    """Notification class for uploaded files by other mediator/client.

    This notification is sent to owner of a resource when
    someone uploads file to shared
    folder.

    Recipients: owner of the document

    """
    signal = documents_signals.document_uploaded_to_folder
    instance_type = documents_models.Document
    runtime_tag = 'document_uploaded'
    title = 'File uploaded'
    deep_link_template = '{base_url}/documents/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/documents/document_uploaded/web.txt'
    )
    push_content_template = (
        'notifications/documents/document_uploaded/push.txt'
    )
    email_subject_template = (
        '{{instance.created_by.full_name}} has uploaded a file '
        'the shared folder'
    )
    email_content_template = (
        'notifications/documents/document_uploaded/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.owner
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get client's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            self.instance.owner_id
        )

    def get_notification_extra_payload(self) -> dict:
        return dict(
            notification_sender=self.instance.created_by.pk,
        )

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        payload = super().prepare_payload(notification, **kwargs)
        payload['notification_sender'] = user_models.AppUser.objects.filter(
            pk=notification.extra_payload.get('notification_sender')
        ).first()
        return payload


class DocumentUploadedToMatterNotificationResource(BaseNotificationResource):
    """Notification class for uploaded files by other mediator/client.

    This notification is sent to owner of a resource when
    someone uploads file to shared
    folder.

    Recipients: owner of the document

    """
    signal = documents_signals.document_uploaded_to_matter
    instance_type = documents_models.Document
    runtime_tag = 'document_uploaded_to_matter'
    title = 'File uploaded to matter'
    deep_link_template = '{base_url}/documents/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/documents/document_uploaded_to_matter/web.txt'
    )
    push_content_template = (
        'notifications/documents/document_uploaded_to_matter/push.txt'
    )
    email_subject_template = (
        '{{instance.created_by.full_name}} has uploaded a file '
        'the matter'
    )
    email_content_template = (
        'notifications/documents/document_uploaded_to_matter/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.created_by
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        if self.instance.created_by.is_client:
            recipents = set(
                self.instance.shared_with.all().values_list('pk', flat=True)
            ).union(
                set([self.instance.matter.mediator.pk])
            )
        elif self.instance.created_by.is_mediator:
            recipents = set(
                self.instance.shared_with.all().values_list('pk', flat=True)
            ).union(
                set([self.instance.matter.client.pk])
            )
        return user_models.AppUser.objects.filter(pk__in=recipents)

    def get_notification_extra_payload(self) -> dict:
        return dict(
            notification_sender=self.instance.created_by.pk,
        )

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        payload = super().prepare_payload(notification, **kwargs)
        payload['notification_sender'] = user_models.AppUser.objects.filter(
            pk=notification.extra_payload.get('notification_sender')
        ).first()
        return payload
