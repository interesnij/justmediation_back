EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = 'sgbackend.SendGridBackend'
DEFAULT_FROM_EMAIL = 'JustMediation <no-reply@justmediation.com>'
