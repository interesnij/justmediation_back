# Rest framework API configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # SessionAuthentication is also used for CSRF
        # validation on ajax calls from the frontend
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.ModelSerializer',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'libs.api.pagination.PageLimitOffsetPagination',
    'EXCEPTION_HANDLER':
        'libs.api.exceptions.custom_exception_handler_simple',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'libs.api.renderers.ReducedBrowsableAPIRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

REST_FRAMEWORK_CUSTOM_FIELD_MAPPING = {
    # Additional fields mappings
    # Configure updating ``ModelSerializer.serializer_field_mapping`` dict
    # When ``libs.apps.LibsAppConfig`` executes
    'django.contrib.gis.db.models.PointField':
        'libs.api.serializers.fields.CustomLocationField',
    'django.db.models.DateTimeField':
        'libs.api.serializers.fields.DateTimeFieldWithTZ'
}

# Django Rest Auth (Rest API Layer) above allauth

REST_AUTH_SERIALIZERS = {
    'TOKEN_SERIALIZER':
        'apps.users.api.serializers.TokenSerializer',
    'PASSWORD_RESET_SERIALIZER':
        'apps.users.api.serializers.AppUserPasswordResetSerializer',
    'USER_DETAILS_SERIALIZER':
        'apps.users.api.serializers.AppUserSerializer',
    'PASSWORD_CHANGE_SERIALIZER':
        'apps.users.api.serializers.AppUserPasswordChangeSerializer',
    'PASSWORD_RESET_CONFIRM_SERIALIZER':
        'apps.users.api.serializers.AppUserPasswordResetConfirmSerializer'
}

# turn off this setting to avoid issues with CSRF validation on login with API
REST_SESSION_LOGIN = False

# Will add old password field for password change serializer
OLD_PASSWORD_FIELD_ENABLED = True
