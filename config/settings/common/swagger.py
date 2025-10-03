from libs.utils import get_latest_version

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
}

API_INFO_BACKEND = {
    'title': 'JustMediation API',
    'default_version': "1",
    'description': 'JustMediation swagger API specification',
}
