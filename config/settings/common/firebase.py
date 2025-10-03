FIREBASE = {
    # this file will be auto added on server with Jenkins build
    # in local it can be get with `inv system.init-firebase` command
    'CREDENTIALS': 'config/google-credentials/credentials.json',
    'CLIENT_NAME': 'Firestore client',
}

FIREBASE_CONFIG = {}

FIREBASE_ENABLED = True

# path to created files with firebase credentials taken from vault
FIREBASE_SETTINGS_FOLDER = 'config/google-credentials/'
FIREBASE_SERVICE_ACCOUNT_FILE = f'{FIREBASE_SETTINGS_FOLDER}credentials.json'
FIREBASE_PROJECT_SETTINGS_FILE = (
    f'{FIREBASE_SETTINGS_FOLDER}project-settings.json'
)

# settings for google credentials files generation
FIREBASE_ENV_CONFIG = {
    # should be separately set for each env from
    # VAULT_FIREBASE_SERVICE_ACCOUNT
    'vault_service_account': '',
    'service_account_file': FIREBASE_SERVICE_ACCOUNT_FILE,
    # should be set for local env only to test Firebase client functionality
    # from VAULT_FIREBASE_PROJECT_SETTINGS
    'vault_project_settings': '',
    'project_settings_file': FIREBASE_PROJECT_SETTINGS_FILE,
}

FCM_FIREBASE_ENABLED = True
# FCM django settings
FCM_DJANGO_SETTINGS = {
    'FCM_SERVER_KEY': None,
    # True if you want to have only one active device per registered
    # user at a time
    # default: False
    'ONE_DEVICE_PER_USER': False,
    # Devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    'DELETE_INACTIVE_DEVICES': False,
    'UPDATE_ON_DUPLICATE_REG_ID': True,
}

# Define extra push notifications params for each notification
PUSH_NOTIFICATIONS_EXTRA_PARAMS = dict(
    new_video_call=dict(
        notification_foreground=False
    )
)
