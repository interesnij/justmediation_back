import mimetypes
from django.urls import reverse_lazy

# инициализируйте mimetypes, чтобы он стал доступен из sOS mimetypes
mimetypes.init()
# https://support.docusign.com/en/guides/ndse-user-guide-supported-file-formats
DOCUSIGN_AVAILABLE_FORMATS = [
    # documents
    '.doc', '.docm', '.docx', '.dot', '.dotm', '.dotx', '.htm', '.html',
    '.msg', '.pdf', '.rtf', '.txt', '.wpd', '.xps',
    # images
    '.bmp', '.gif', '.jpg', '.jpeg', '.png', '.tif', '.tiff',
    # presentations
    '.pot', '.potx', '.pps', '.ppt', '.pptm', '.pptx',
    # spreadsheets
    '.csv', '.xls', '.xlsm', '.xlsx',
]


ABSENT_FORMATS = {
    '.msg': 'application/vnd.ms-outlook',
    '.xps': 'application/vnd.ms-xpsdocument',
}


DOCUSIGN_AVAILABLE_MIME_TYPES = [
    mimetypes.types_map.get(ext, None)
    if ext in mimetypes.types_map else ABSENT_FORMATS.get(ext)
    for ext in DOCUSIGN_AVAILABLE_FORMATS
]


DOCUSIGN = {
    'TOKEN_EXPIRATION': 3600,  # in seconds
    # Should be overridden for environment
    'PRIVATE_RSA_KEY': None,
    'DRAFT_ENVELOPE_EMAIL_SUBJECT': 'Please sign this document set',

    # Should be overridden for environment
    # base url of docusign
    'BASE_PATH': None,
    # base oauth host on docusign
    'OAUTH_HOST_NAME': None,
    'INTEGRATION_KEY': None,
    'SECRET_KEY': None,
    'CONSENT_REDIRECT_URL': reverse_lazy('v1:callbacks-save-consent'),
    'ENVELOPE_STATUS_WEBHOOK_URL': reverse_lazy(
        'v1:callbacks-update-envelope-status'
    )
}
