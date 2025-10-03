from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from libs.docusign.constants import ENVELOPE_STATUS_SENT, ENVELOPE_STATUSES

from apps.core.api.serializers import BaseSerializer
from apps.core.fields.any_scheme_url import AnySchemeURLSerializerField

from ..adapters import DocuSignAdapter
from ..models import Envelope, ESignDocument, ESignProfile

__all__ = (
    'ESignDocumentSerializer',
    'EnvelopeShortSerializer',
    'EnvelopeSerializer',
    'ESignProfileSerializer',
    'SaveUserConsentSerializer',
    'UpdateEnvelopeStatusSerializer',
    'ReturnURLSerializer',
    'RequiredReturnURLSerializer',
)


class ReturnURLSerializer(serializers.Serializer):
    """Simple serializer which returns `return_url` field only.

    This serializer is used in to make DocuSign related callbacks.

    """
    return_url = AnySchemeURLSerializerField(required=False)


class RequiredReturnURLSerializer(serializers.Serializer):
    """Simple serializer which returns `return_url` field only.

    This serializer is used in to make DocuSign related callbacks and defines
    `required` return url field.

    """
    return_url = AnySchemeURLSerializerField()


class ESignDocumentSerializer(BaseSerializer):
    """Base serializer for esign documents."""

    class Meta:
        model = ESignDocument
        fields = (
            'id',
            'file',
            'order',
            'name',
        )
        extra_kwargs = {
            'name': {'required': False}
        }


class EnvelopeShortSerializer(BaseSerializer):
    """Shorten serializer for Envelope model."""
    documents = ESignDocumentSerializer(many=True)

    class Meta:
        model = Envelope
        fields = (
            'id',
            'docusign_id',
            'matter',
            'status',
            'type',
            'documents',
        )
        read_only_fields = (
            'id',
            'docusign_id',
            'status',
        )
        extra_kwargs = {'type': {'required': True}}

    def get_fields(self):
        """Restrict matter's qs to only available for user matters."""
        fields = super().get_fields()
        if not self.user or not self.user.is_authenticated:
            return fields
        fields['matter'].queryset = fields['matter'].queryset \
            .available_for_user(self.user)
        return fields

    def validate(self, attrs):
        """Set up reverse Envelope relation for `documents`."""
        documents = attrs.pop('documents')
        attrs = super().validate(attrs)
        attrs['documents'] = [doc['file'] for doc in documents]
        return attrs

    def create(self, validated_data):
        """Custom create action for Envelope."""
        adapter = self.context['adapter']
        envelope = adapter.create_envelope(
            matter=validated_data['matter'],
            documents=validated_data['documents'],
            type=validated_data['type']
        )
        return envelope


class EnvelopeSerializer(EnvelopeShortSerializer):
    """Serializer for Envelope model."""
    edit_link = serializers.SerializerMethodField()

    class Meta(EnvelopeShortSerializer.Meta):
        fields = EnvelopeShortSerializer.Meta.fields + ('edit_link',)

    def get_edit_link(self, obj):
        """Get Envelope `edit` link from DocuSign."""
        adapter = self.context['adapter']
        return_url = self.context.get('return_url')
        return adapter.get_envelope_edit_link(
            envelope=obj,
            return_url=return_url
        )


class ESignProfileSerializer(BaseSerializer):
    """Serializer for ESignProfile model."""

    has_consent = serializers.ReadOnlyField()
    obtain_consent_link = serializers.ReadOnlyField()

    class Meta:
        model = ESignProfile
        fields = (
            'docusign_id',
            'has_consent',
            'obtain_consent_link',
        )

    def to_representation(self, instance):
        """Prepare instance before its representation."""
        adapter = DocuSignAdapter(user=instance.user)
        return_url = self.context['return_url']
        instance.has_consent = adapter.is_consent_obtained()
        instance.obtain_consent_link = '' if instance.has_consent \
            else adapter.get_consent_link(return_url)
        return super().to_representation(instance)


class SaveUserConsentSerializer(serializers.Serializer):
    """Serializer which validates request data before making user consent save.

    In case if user agrees with obtaining consent - serializer accepts `state`
    and `code` params, otherwise there will be returned `state`, `error` and
    `error_message`. So `code` parameter is not required.

    """
    code = serializers.CharField(required=False)
    state = serializers.CharField()


class UpdateEnvelopeStatusSerializer(serializers.Serializer):
    """Serializer which validates request data on envelope status updates.

    This data comes from DocuSign in its specific format, when Envelope status
    is changed.

    """
    EnvelopeID = serializers.CharField()
    Status = serializers.ChoiceField(
        # use both lower and capitalized choices values, suddenly DocuSign
        # sends some statuses as lower and some as capitalized
        choices=ENVELOPE_STATUSES + [
            status.capitalize() for status in ENVELOPE_STATUSES
        ],
    )

    def validate(self, attrs):
        """Validate DocuSign data for Envelope status update."""
        attrs = super().validate(attrs)
        attrs['envelope'] = Envelope.objects.filter(
            docusign_id=attrs['EnvelopeID']
        ).first()
        attrs['status'] = attrs['Status'].lower()
        if not attrs['envelope']:
            raise ValidationError(
                f"No envelope with `{attrs['EnvelopeID']}` was found in DB"
            )
        return attrs

    def save(self, **kwargs):
        """Save new envelope status."""
        status = self.validated_data['status']
        envelope = self.validated_data['envelope']

        # don't decrease Envelope `status` if `sent` callback comes later
        # `completed` or any other one. suddenly `sent` status callback takes
        # about 20-30s and documents set can become completed till that time
        if status == ENVELOPE_STATUS_SENT and not envelope.is_created:
            return envelope

        # make envelope `status` update with its special transition
        transition_name = Envelope.STATUS_TRANSITION_MAP[status]
        getattr(envelope, transition_name)()
        envelope.save()
        return envelope
