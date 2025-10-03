# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
logging_format = (
    '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': logging_format
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'stripe_log': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/stripe.log',
        },
        #'docusign_log': {
        #    'level': 'ERROR',
        #    'class': 'logging.FileHandler',
        #    'filename': '/var/log/docusign.log',
        #},
        'quickbooks_log': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/quickbooks.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'stripe': {
            'handlers': ['stripe_log'],
            'level': 'ERROR',
            'propagate': True,
            'formatter': 'minimal',
        },
    }
}
