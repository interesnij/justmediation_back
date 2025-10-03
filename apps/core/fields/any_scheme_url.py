import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, _lazy_re_compile
from django.db import models
from django.forms.fields import CharField, URLField
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

__all__ = (
    'AnySchemeURLValidator',
    'AnySchemeURLFormField',
    'AnySchemeURLModelField',
    'AnySchemeURLSerializerField',
)


class AnySchemeURLValidator(URLValidator):
    """Overridden `URLValidator` which provides adding URLs with any schemes.

    This validator can be used in serializer, form and even model fields where
    it is needed.

    """

    def __init__(self, *args, **kwargs):
        """Change main regex - now `host` parameter is not required.

        Also `end of the string` symbol is removed at the end of regex as it
        doesn't match otherwise.

        """
        super().__init__(*args, **kwargs)
        self.regex = _lazy_re_compile(
            r'^(?:[a-z0-9\.\-\+]*)://'
            r'(?:\S+(?::\S*)?@)?'
            r'(?:' + self.ipv4_re + '|' + self.ipv6_re + '|'
            + self.host_re + ')?'  # change is here - added `?` at the end
            r'(?::\d{2,5})?'
            r'(?:[/?#][^\s]*)?',
            re.IGNORECASE)

    def __call__(self, value):
        """Validate depending on `schema` existence.

        If schema was added - validate `url` as usual, else - validate that
        `url` starts with slash only.

        """
        scheme = value.split('://')[0].lower() if '://' in value else None
        if scheme and scheme not in self.schemes:
            self.schemes.append(scheme)

        # if schema was added
        if scheme:
            super().__call__(value)
            return

        # if no schema was added
        if value[0] != '/':
            raise ValidationError(self.message, code=self.code)


class AnySchemeURLFormField(URLField):
    """Overridden form URL field which allows to add URLs with any scheme.

    It is a form field, which allows to set any scheme in URL.

    Usage:
        class Person (forms.ModelForm):
            url = AnySchemeURLFormField()

    """
    default_validators = [AnySchemeURLValidator()]

    def to_python(self, value):
        """Remove adding `http` scheme and `//` if no scheme was set

        Prevent all URL transformations and send it as it is

        """
        return super(CharField, self).to_python(value)


class AnySchemeURLModelField(models.URLField):
    """Overridden model `URLField` provides possibility for different schemes.

    It is a model field, which allows to set any scheme in URL.

    Usage:
        class Person (models.Model):
            url = AnySchemeURLModelField()

    """
    default_validators = [AnySchemeURLValidator()]

    def formfield(self, **kwargs):
        """Override `form_class` for custom URL field

        It's not enough to override `default_validators` of a field as it won't
        override `default_validator` in for field. So here we add custom
        `form_class` for URL field with the same validator.

        """
        return super().formfield(**{
            'form_class': AnySchemeURLFormField
        })


class AnySchemeURLSerializerField(serializers.CharField):
    """URLField which allows to set custom `AnyScheme` url validator.

    It is a serializer field, which allows to set any scheme in URL.

    Usage:
        class Person (serializers.Serializer):
            url = AnySchemeURLSerializerField()

    """
    default_error_messages = {
        'invalid': _('Enter a valid URL.')
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validator = AnySchemeURLValidator(
            message=self.error_messages['invalid']
        )
        self.validators.append(validator)
