from django.db.models import QuerySet

from ....business import models as business_models
from ....business import signals as business_signals
from ....core.models import BaseModel
from ....users import models as user_models
from ... import models
from .base import BaseNotificationResource


class NewMessageNotificationResource(BaseNotificationResource):
    """Notification class for new matter's messages.

    This notification is sent when mediator or client creates a new post
    in matter's topic.

    Recipients: Mediators and clients

    In designs it's `New Message` notification type of of group 'Matters'.

    """
    signal = business_signals.new_message
    instance_type = business_models.MatterComment
    runtime_tag = 'new_message'
    title = 'New message'
    deep_link_template = '{base_url}/matters/messages/{id}'
    id_attr_path: str = 'post_id'
    web_content_template = (
        'notifications/business/new_message/web.txt'
    )
    push_content_template = (
        'notifications/business/new_message/push.txt'
    )
    email_subject_template = (
        '{% if recipient.is_mediator %}'
        '{{instance.author.display_name}} sent you a new message '
        'in {{ instance.post.matter.title }}'
        '{% else %}'
        'New message from {{instance.author.display_name}} '
        'in {{instance.post.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/new_message/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.author
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        available_members = \
            self.instance.post.participants.values_list('pk', flat=True)
        recipents = set(
            self.instance.participants.exclude(
                id=self.user.pk
            ).filter(
                id__in=available_members
            ).values_list('pk', flat=True)
        )
        return user_models.AppUser.objects.filter(
            pk__in=recipents
        )


class NewChatNotificationResource(BaseNotificationResource):
    """Notification class for new chats(leads).

    This notification is sent to mediator or client when creator of lead
    creates lead with this mediator or client.

    Recipients: mediators and clients

    In designs it's `New Chats` notification type.

    """
    signal = business_signals.new_lead
    instance_type = business_models.Lead
    runtime_tag = 'new_chat'
    title = 'New chat'
    deep_link_template = '{base_url}/chats?chatId={id}'
    id_attr_path: str = 'chat_channel'
    web_content_template = (
        'notifications/business/new_chat/web.txt'
    )
    push_content_template = (
        'notifications/business/new_chat/push.txt'
    )
    email_subject_template = (
        '{% if recipient.is_mediator %}'
        '{{instance.client.display_name}} sent you a new chat'
        '{% else %}'
        'New Chat message from {{instance.mediator.display_name}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/new_chat/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add lead creator."""
        self.created_by: user_models.AppUser = kwargs['created_by']
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get mediator or client user profile as queryset.

        Get mediator or client user profile as queryset depending on who
        created lead.

        """
        users_qs = user_models.AppUser.objects.all()
        if self.created_by.is_mediator:
            return users_qs.filter(pk=self.instance.client.pk)
        return users_qs.filter(pk=self.instance.mediator.pk)


class NewVideoCallResource(BaseNotificationResource):
    """Notification class for video call's messages.

    This notification is sent to participants of video chat, when
    it's created.

    Recipients: mediators and clients

    """
    signal = business_signals.new_video_call
    instance_type = business_models.VideoCall
    runtime_tag = 'new_video_call'
    title = 'New video call'
    web_content_template = (
        'notifications/business/new_video_call/web.txt'
    )
    push_content_template = (
        'notifications/business/new_video_call/push.txt'
    )
    email_subject_template = (
        'Invitation to a video call.'
    )
    email_content_template = (
        'notifications/business/new_video_call/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add caller."""
        self.caller: user_models.AppUser = kwargs['caller']
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    @classmethod
    def get_deep_link(cls, payload: dict) -> str:
        """Get link to video chat."""
        return payload['instance'].call_url

    def get_recipients(self) -> QuerySet:
        """Get all participants of call except caller as queryset."""
        return self.instance.participants.exclude(pk=self.caller.pk)

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        payload = super().prepare_payload(notification, **kwargs)
        participants = payload['instance'].participants
        payload['other_participants'] = participants.exclude(
            pk=payload['recipient'].pk
        )
        return payload


class NewMatterResource(BaseNotificationResource):
    """Notification class for new matter.

    This notification is sent when matter was new matter is created.

    Recipients: mediators and Support

    """
    signal = business_signals.new_matter
    instance_type = business_models.Matter
    runtime_tag = 'new_matter'
    title = 'New Matter'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'pk'
    web_content_template = (
        'notifications/business/new_matter/web.txt'
    )
    push_content_template = (
        'notifications/business/new_matter/push.txt'
    )
    email_subject_template = (
        'A new matter is created'
    )
    email_content_template = (
        'notifications/business/new_matter/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.client.pk
        )


class MatterStatusUpdateNotificationResource(BaseNotificationResource):
    """Notification class for matter status updates.

    This notification is sent to client when mediator changes status of
    client's matter.

    Recipients: Only client

    In designs it's `Status Update` notification type of group 'Matters'.

    """
    signal = business_signals.matter_status_update
    instance_type = business_models.Matter
    runtime_tag = 'matter_status_update'
    title = 'Matter status update'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'pk'
    web_content_template = (
        'notifications/business/matter_status_update/web.txt'
    )
    push_content_template = (
        'notifications/business/matter_status_update/push.txt'
    )
    email_subject_template = (
        'Matter status change from '
        '{{ instance.mediator.display_name }} on {{ instance.title }}'
    )
    email_content_template = (
        'notifications/business/matter_status_update/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Remember `new_status` which was get from a signal."""
        self.user: user_models.AppUser = instance.mediator.user
        self.new_status = kwargs['new_status']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get client's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.client.pk
        )

    def get_notification_extra_payload(self) -> dict:
        """Extend notification `extra_payload` with `new_status`.

        It is needed for correct rendering notifications in API, so `status`
        in message wouldn't change on Matter's later status updates.

        """
        extra_payload = super().get_notification_extra_payload()
        extra_payload['new_status'] = self.new_status
        return extra_payload


class MatterSharedResource(BaseNotificationResource):
    """Notification class for shared matter.

    This notification is sent when matter was shared with mediator.

    Recipients: mediators and Support

    In designs it's `New Matter Shared` notification type of group  'Matters'.

    """
    signal = business_signals.new_matter_shared
    instance_type = business_models.MatterSharedWith
    runtime_tag = 'new_matter_shared'
    title = 'New Matter Shared'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'matter_id'
    web_content_template = (
        'notifications/business/new_matter_shared/web.txt'
    )
    push_content_template = (
        'notifications/business/new_matter_shared/push.txt'
    )
    email_subject_template = (
        '{% if inviter %}'
        'New shared matter from {{inviter.full_name}}'
        '{% else %}'
        # Just in case if we would have non existing user id
        # Since inviter is not saved in MatterSharedWith and adding it is
        # troublesome(since it's m2m relation). We save it in as id in the
        # notification payload. Added these checks just to be save.
        'justmediationhub - New shared matter {{instance.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/new_matter_shared/email.html'
    )

    def __init__(
        self,
        instance: business_models.MatterSharedWith,
        inviter: user_models.AppUser,
        title: str,
        message: str,
        **kwargs,
    ):
        """Add inviter and it's message and title to class."""
        self.title = title
        self.inviter = inviter
        self.message = message
        self.user: user_models.AppUser = instance.matter.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.user_id
        )

    def get_notification_extra_payload(self) -> dict:
        """Add inviter's id and it's message and title to extra payload."""
        return dict(
            title=self.title,
            inviter_id=self.inviter.pk,
            message=self.message,
        )

    @classmethod
    def prepare_payload(
        cls,
        notification: models.Notification,
        **kwargs
    ) -> dict:
        payload = super().prepare_payload(notification, **kwargs)
        payload['inviter'] = user_models.AppUser.objects.filter(
            pk=notification.extra_payload.get('inviter_id')
        ).first()
        return payload


class MatterReferredResource(BaseNotificationResource):
    """Notification class for referred matter.

    This notification is sent when matter was referred with mediator.

    Recipients: mediators

    In designs it's `New Matter Referred`
    notification type of group  'Matters'.

    """
    signal = business_signals.new_matter_referred
    instance_type = business_models.Matter
    runtime_tag = 'new_matter_referred'
    title = 'New Matter Referred'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/new_matter_referred/web.txt'
    )
    push_content_template = (
        'notifications/business/new_matter_referred/push.txt'
    )
    email_subject_template = (
        '{% if notification_sender %}'
        'New matter referred from {{notification_sender.full_name}}'
        '{% else %}'
        # Just in case if we would have non existing user id
        # Since inviter is not saved in MatterSharedWith and adding it is
        # troublesome(since it's m2m relation). We save it in as id in the
        # notification payload. Added these checks just to be save.
        'justmediationhub - New referred matter {{instance.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/new_matter_referred/email.html'
    )

    def __init__(
        self,
        instance: business_models.Matter,
        notification_sender: user_models.AppUser,
        **kwargs,
    ):
        """Add inviter and it's message and title to class."""
        self.notification_sender = notification_sender
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.referral.mediator.user_id
        )

    def get_notification_extra_payload(self) -> dict:
        """Add inviter's id and it's message and title to extra payload."""
        return dict(
            message=self.instance.referral.message,
            notification_sender=self.notification_sender.pk,
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


class ReferralAcceptedResource(BaseNotificationResource):
    """Notification class for accepted referred matter.

    This notification is sent when matter referred with mediator is accepted.

    Recipients: mediators

    In designs it's `New Matter Referred`
    notification type of group  'Matters'.

    """
    signal = business_signals.new_referral_accepted
    instance_type = business_models.Matter
    runtime_tag = 'new_referral_accepted'
    title = 'Referral Accepted'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/matter_referral_accepted/web.txt'
    )
    push_content_template = (
        'notifications/business/matter_referral_accepted/push.txt'
    )
    email_subject_template = (
        '{% if acceptor %}'
        'Referral accepted from {{acceptor.full_name}}'
        '{% else %}'
        # Just in case if we would have non existing user id
        # Since inviter is not saved in MatterSharedWith and adding it is
        # troublesome(since it's m2m relation). We save it in as id in the
        # notification payload. Added these checks just to be save.
        'justmediationhub - Matter referral accepted {{instance.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/matter_referral_accepted/email.html'
    )

    def __init__(
        self,
        instance: business_models.Matter,
        notification_sender: user_models.AppUser,
        **kwargs,
    ):
        """Add inviter and it's message and title to class."""
        self.notification_sender = notification_sender
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.mediator.user_id
        )

    def get_notification_extra_payload(self) -> dict:
        """Add inviter's id and it's message and title to extra payload."""
        return dict(
            notification_sender=self.notification_sender.pk,
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


class ReferralDeclinedResource(BaseNotificationResource):
    """Notification class for declined referred matter.

    This notification is sent when matter referred with mediator is declined.

    Recipients: mediators

    In designs it's `Referral declined` notification type of group  'Matters'.

    """
    signal = business_signals.new_referral_declined
    instance_type = business_models.Matter
    runtime_tag = 'new_referral_declined'
    title = 'Referral Declined'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/matter_referral_declined/web.txt'
    )
    push_content_template = (
        'notifications/business/matter_referral_declined/push.txt'
    )
    email_subject_template = (
        '{% if notification_sender %}'
        'Referral declined by {{notification_sender.full_name}}'
        '{% else %}'
        # Just in case if we would have non existing user id
        # Since inviter is not saved in MatterSharedWith and adding it is
        # troublesome(since it's m2m relation). We save it in as id in the
        # notification payload. Added these checks just to be save.
        'justmediationhub - Matter referral declined {{instance.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/matter_referral_declined/email.html'
    )

    def __init__(
        self,
        instance: business_models.Matter,
        notification_sender: user_models.AppUser,
        **kwargs,
    ):
        """Add inviter and it's message and title to class."""
        self.notification_sender = notification_sender
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.mediator.user_id
        )

    def get_notification_extra_payload(self) -> dict:
        """Add inviter's id and it's message and title to extra payload."""
        return dict(
            notification_sender=self.notification_sender.pk,
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


class ReferralRevokedResource(BaseNotificationResource):
    """Notification class for referred matter.

    This notification is sent when matter was referred with mediator.

    Recipients: mediators

    In designs it's `New Matter Referred`
    notification type of group  'Matters'.

    """
    signal = business_signals.matter_referral_revoked
    instance_type = business_models.Matter
    runtime_tag = 'matter_referral_revoked'
    title = 'Matter Referral Referred'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/matter_referral_revoked/web.txt'
    )
    push_content_template = (
        'notifications/business/matter_referral_revoked/push.txt'
    )
    email_subject_template = (
        '{% if notification_sender %}'
        'Matter referral revoked from {{notification_sender.full_name}}'
        '{% else %}'
        # Just in case if we would have non existing user id
        # Since inviter is not saved in MatterSharedWith and adding it is
        # troublesome(since it's m2m relation). We save it in as id in the
        # notification payload. Added these checks just to be save.
        'justmediationhub - revoked matter {{instance.matter.title}}'
        '{% endif %}'
    )
    email_content_template = (
        'notifications/business/matter_referral_revoked/email.html'
    )

    def __init__(
        self,
        instance: business_models.Matter,
        notification_sender: user_models.AppUser,
        **kwargs,
    ):
        """Add inviter and it's message and title to class."""
        self.notification_sender = notification_sender
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.referral.mediator.user_id
        )

    def get_notification_extra_payload(self) -> dict:
        """Add inviter's id and it's message and title to extra payload."""
        return dict(
            message=self.instance.referral.message,
            notification_sender=self.notification_sender.pk,
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


class MatterStageUpdateNotificationResource(BaseNotificationResource):
    """Notification class for matter stage updates.

    This notification is sent to client when mediator changes stage of
    client's matter.

    Recipients: Only client

    In designs it's `Status Update` notification type of group 'Matters'.

    """
    signal = business_signals.matter_stage_update
    instance_type = business_models.Matter
    runtime_tag = 'matter_stage_update'
    title = 'Matter stage update'
    deep_link_template = '{base_url}/matters/{id}'
    id_attr_path: str = 'pk'
    web_content_template = (
        'notifications/business/matter_stage_update/web.txt'
    )
    push_content_template = (
        'notifications/business/matter_stage_update/push.txt'
    )
    email_subject_template = (
        'Matter stage changed to '
        '{{ instance.stage.title }} on {{ instance.title }}'
    )
    email_content_template = (
        'notifications/business/matter_stage_update/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add sender."""
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get client's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.client.pk
        )

    def get_notification_extra_payload(self) -> dict:
        """Extend notification `extra_payload` with `new_status`.

        It is needed for correct rendering notifications in API, so `status`
        in message wouldn't change on Matter's later status updates.

        """
        extra_payload = super().get_notification_extra_payload()
        return extra_payload


class NewProposalNotificationResource(BaseNotificationResource):
    """Notification class for new proposal.

    This notification is sent when mediator submits a new proposal
    on posted-matter.

    Recipients: clients
    """
    signal = business_signals.new_proposal
    instance_type = business_models.Proposal
    runtime_tag = 'new_proposal'
    title = 'New Proposal Submitted'
    deep_link_template = '{base_url}/business/proposals/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/new_proposal/web.txt'
    )
    push_content_template = (
        'notifications/business/new_proposal/push.txt'
    )
    email_subject_template = (
        '{{ instance.mediator.full_name }} '
        'has submitted a proposal on the '
        '{{instance.post.title}}.'
    )
    email_content_template = (
        'notifications/business/new_proposal/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.post.client.pk
        )


class ProposalWithDrawnNotificationResource(BaseNotificationResource):
    """Notification class for withdrawn proposal.

    This notification is sent when mediator submits a new proposal
    on posted-matter.

    Recipients: clients
    """
    signal = business_signals.proposal_withdrawn
    instance_type = business_models.Proposal
    runtime_tag = 'proposal_withdrawn'
    title = 'Proposal Withdrawn'
    deep_link_template = '{base_url}/business/proposals/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/proposal_withdrawn/web.txt'
    )
    push_content_template = (
        'notifications/business/proposal_withdrawn/push.txt'
    )
    email_subject_template = (
        '{{ instance.mediator.full_name }} has withdrawn '
        'proposal he submitted on the {{instance.post.title}}.'
    )
    email_content_template = (
        'notifications/business/proposal_withdrawn/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.post.client.pk
        )


class ProposalAcceptedNotificationResource(BaseNotificationResource):
    """Notification class for accepted proposal.

    This notification is sent when client accepts mediator proposal
    on posted-matter.

    Recipients: mediators
    """
    signal = business_signals.proposal_accepted
    instance_type = business_models.Proposal
    runtime_tag = 'proposal_accepted'
    title = 'Proposal Accepted'
    deep_link_template = '{base_url}/business/proposals/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/proposal_accepted/web.txt'
    )
    push_content_template = (
        'notifications/business/proposal_accepted/push.txt'
    )
    email_subject_template = (
        'Your proposal on the {{instance.post.title}} has been accepted.'
    )
    email_content_template = (
        'notifications/business/proposal_accepted/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.mediator.pk
        )


class PostDeactivatedNotificationResource(BaseNotificationResource):
    """Notification class for deactivated posted matters.

    This notification is sent when client deactivates posted-matter.

    Recipients: mediators
    """
    signal = business_signals.post_inactivated
    instance_type = business_models.PostedMatter
    runtime_tag = 'post_deactivated'
    title = 'Posted Matter Deactivated'
    deep_link_template = '{base_url}/business/posted-matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/post_deactivated/web.txt'
    )
    push_content_template = (
        'notifications/business/post_deactivated/push.txt'
    )
    email_subject_template = (
        '{{ instance.client.full_name }} has deactivated {{instance.title}}.'
    )
    email_content_template = (
        'notifications/business/post_deactivated/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk__in=self.instance.proposals.values_list(
                'mediator_id', flat=True
            )
        )


class PostReactivatedNotificationResource(BaseNotificationResource):
    """Notification class for reactivated posted matters.

    This notification is sent when client reactivates posted-matter.

    Recipients: mediators
    """
    signal = business_signals.post_reactivated
    instance_type = business_models.PostedMatter
    runtime_tag = 'post_reactivated'
    title = 'Posted Matter Reactivated'
    deep_link_template = '{base_url}/business/posted-matters/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/post_reactivated/web.txt'
    )
    push_content_template = (
        'notifications/business/post_reactivated/push.txt'
    )
    email_subject_template = (
        '{{ instance.client.full_name }} has reactivated {{instance.title}}.'
    )
    email_content_template = (
        'notifications/business/post_reactivated/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = kwargs['user']
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk__in=self.instance.proposals.values_list(
                'mediator_id', flat=True
            )
        )


class NewInvoiceNotificationResource(BaseNotificationResource):
    """Notification class for new invoice

    This notification is sent when mediator creates an new invoice
    inside matter.

    Recipients: clients

    """
    signal = business_signals.invoice_is_created
    instance_type = business_models.Invoice
    runtime_tag = 'new_invoice'
    title = 'New invoice'
    deep_link_template = '{base_url}/matters/invoice/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/invoice_created/web.txt'
    )
    push_content_template = (
        'notifications/business/invoice_created/push.txt'
    )
    email_subject_template = (
        'New invoice from {{instance.matter.mediator.display_name}}'
    )
    email_content_template = (
        'notifications/business/invoice_created/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.matter.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk=self.instance.matter.client.pk
        )

    def get_notification_extra_payload(self) -> dict:
        return dict(
            invoice_sender_email=self.instance.email,
        )


class NewBillingItemNotificationResource(BaseNotificationResource):
    """Notification class for new billing item

    This notification is sent when mediator creates an new billing item
    inside matter.

    Recipients: clients

    """
    signal = business_signals.billing_item_is_created
    instance_type = business_models.BillingItem
    runtime_tag = 'new_billing_item'
    title = 'New billing item'
    deep_link_template = '{base_url}/matters/billing-item/{id}'
    id_attr_path: str = 'id'
    web_content_template = (
        'notifications/business/billing_item_created/web.txt'
    )
    push_content_template = (
        'notifications/business/billing_item_created/push.txt'
    )
    email_subject_template = (
        'New billing item from {{instance.matter.mediator.display_name}}'
    )
    email_content_template = (
        'notifications/business/billing_item_created/email.html'
    )

    def __init__(self, instance: BaseModel, **kwargs):
        """Add user."""
        self.user: user_models.AppUser = instance.matter.mediator.user
        super().__init__(instance, **kwargs)

    def get_recipients(self) -> QuerySet:
        """Get recipient's user profile as queryset."""
        return user_models.AppUser.objects.filter(
            pk__in=self.instance.matter.shared_with.all().values_list(
                'pk', flat=True
            )
        )
