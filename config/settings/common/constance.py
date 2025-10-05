from collections import OrderedDict
from decimal import Decimal
from django.forms import fields

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

# Custom settings for constance fields
# You can set up your custom field with settings you need for constance setting
# Example:
# 'name_of_field' : [
#   path to a field class(field for form like django.forms),
#  (settings for field will be passed at field class __init__)
#  {
#    'widget':  like 'django.forms.widgets.Textarea',
#    'widget_kwargs': (will passed to widget __init__),
#     and so on.
#  }
# ]

CONSTANCE_ADDITIONAL_FIELDS = dict(
    url_field=[
        'django.forms.URLField', {
            'widget': 'django.forms.widgets.Textarea',
        }
    ],
    percent_field=[
        'django.forms.DecimalField', dict(
            max_value=Decimal(100.00),
            min_value=Decimal(0.1),
            max_digits=5,
            decimal_places=2
        )
    ],
    fee_field=[
        'django.forms.DecimalField', dict(
            min_value=Decimal(1.0),
            max_digits=5,
            decimal_places=2
        )
    ],
    invite_link_field=[
        'libs.fields.URLTemplateField', dict(
            widget='django.forms.widgets.Textarea',
            keys=['domain', 'invite'],
        )
    ],
    password_reset_link_field=[
        'libs.fields.URLTemplateField', dict(
            widget='django.forms.widgets.Textarea',
            keys=['domain', 'user_id', 'token'],
        )
    ],
    staff_field=[
        'django.contrib.postgres.forms.SimpleArrayField', dict(
             base_field=fields.EmailField(),
             widget='django.forms.widgets.Textarea'
        )
    ]
)

CONSTANCE_CONFIG = dict(
    APP_LABEL=(
        'justmediationhub',
        "App's label",
    ),
    ADMINS=(
        ['root@root.com'],
        "Admins' emails to send notifications (divided by commas)",
        'staff_field'
    ),
    MAINTAINERS=(
        ['root@root.com'],
        "Maintainers' emails to send notifications (divided by commas)",
        'staff_field'
    ),
    BASE_OBTAIN_CONSENT_REDIRECT_URL=(
        '',
        'Base redirect url after obtaining consent. It is used by default '
        'when user tries to obtain a consent without `redirect_url` for some'
        'reason.',
        'url_field'
    ),
    CLIENT_INVITE_REDIRECT_LINK=(
        '{domain}/auth/register/client?'
        'invite={invite}',
        'URL template used to redirect client from invite email to register'
        'form',
        'invite_link_field'
    ),
    MEDIATOR_INVITE_REDIRECT_LINK=(
        '{domain}/auth/register/mediator?'
        'invite={invite}',
        'URL template used to redirect mediator from invite email to register'
        'form',
        'invite_link_field'
    ),
    PASSWORD_RESET_REDIRECT_LINK=(
        '{domain}/auth/password-change-confirm?'
        'key={user_id}-{token}',
        'URL template used to redirect user from password reset email to '
        'change password form',
        'password_reset_link_field'
    ),
    DEV_FRONTEND_LINK=(
        'https://app.dev.jus-law.com/',
        'Development Frontend url',
        'url_field'
    ),
    STAGING_FRONTEND_LINK=(
        'https://app.staging.jus-law.com/',
        'Staging frontend url',
        'url_field'
    ),
    PROD_FRONTEND_LINK=(
        'https://app.justmediationhub.com/',
        'Prod frontend url',
        'url_field'
    ),
    APPLICATION_FEE=(
        Decimal(5.0),
        'Application fees for payments',
        'percent_field'
    ),
    # fee for support users
    USER_FEE=(
        Decimal(50.0),
        'Fee for user access',
        'fee_field'
    ),
)

CONSTANCE_CONFIG_FIELDSETS = {
    'General Options': (
        'APP_LABEL',
        'ADMINS',
        'MAINTAINERS',
    ),
    'Esign': (
        'BASE_OBTAIN_CONSENT_REDIRECT_URL',
    ),
    'Auth links': (
        'CLIENT_INVITE_REDIRECT_LINK',
        'MEDIATOR_INVITE_REDIRECT_LINK',
        'PASSWORD_RESET_REDIRECT_LINK',
    ),
    'Finance': (
        'APPLICATION_FEE',
        'USER_FEE',
    ),
    'Frontend': (
        'DEV_FRONTEND_LINK',
        'STAGING_FRONTEND_LINK',
        'PROD_FRONTEND_LINK',
    )
}
# Convert to ordered dict to save ordering in admin
# There is a bug in constance since dicts in python now ordered
CONSTANCE_CONFIG_FIELDSETS = OrderedDict(CONSTANCE_CONFIG_FIELDSETS)
