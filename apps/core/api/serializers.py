import copy

from rest_framework import serializers

from apps.users.models import AppUser


class BaseSerializer(serializers.ModelSerializer):
    """Serializer that validates data using model's clean method."""

    def __init__(self, *args, **kwargs):
        """Set current user."""
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        self.user: AppUser = request.user if request else None

    def get_instance(self):
        """Get instance depending on request."""
        if self.instance:  # if it's update request
            return copy.copy(self.instance)
        return self.Meta.model()  # it's create request

    def prepare_instance(self, attrs):
        """Prepare instance depending on create/update.

        If `create` used, create empty instance and set fields' values with
        received data.
        If `update` used, update existing instance with received data.
        """
        # Prepare instance depending on create/update
        instance = self.get_instance()

        # Get instance related fields' names
        relations = getattr(self.Meta, 'relations', set())

        # Set new data for instance, while ignoring relations
        for attr, value in attrs.items():
            if attr not in relations:
                setattr(instance, attr, value)

        return instance

    def validate(self, attrs):
        """Call model's `.clean()` method during validation.

        Create:
            Just create model instance using provided data.
        Update:
            `self.instance` contains instance with new data. We apply passed
            data to it and then call `clean` method for this temp instance.
        """
        attrs = super().validate(attrs)

        instance = self.prepare_instance(attrs)

        instance.clean()

        return attrs

    def get_fields_to_hide(self, instance) -> tuple:
        """Get fields that should be hidden.

        In some cases we need to hide some fields, but without removing
        fields or creating new serializers(because for front-end it would like
        another model in swagger spec). Here you can define depending on user
        and instance, which fields should be hidden. Fields that should be
        hidden for anonymous should be stated in Meta class of serializer.

        Example: Only Mediator can see it's own registration_attachments, all
        user(even anonymous one) can get a list of Mediators.

        """
        if self.user and self.user.is_anonymous:
            return tuple(getattr(self.Meta, 'fields_to_hide', tuple()))
        return tuple()

    def to_representation(self, instance):
        """Hide fields from fields_to_hide by setting it's value to None."""
        data = super().to_representation(instance=instance)
        fields_to_hide = set(self.get_fields_to_hide(instance=instance))
        for field in fields_to_hide:
            if field not in data:
                continue
            data[field] = None
        return data
