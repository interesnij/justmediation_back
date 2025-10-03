# Application definition
from .health_check import HEALTH_CHECKS_APPS

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.gis',
    'cacheops',
    'corsheaders',
    #'storages',
    'taggit',
    'taggit_labels',
    'imagekit',
    'allauth',
    'allauth.account',
    # Needed: https://github.com/pennersr/django-allauth/issues/1817
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'taggit_serializer',
    'rest_auth',
    'rest_auth.registration',
    'drf_yasg',
    'cities_light',
    'django_object_actions',
    'django_filters',
    'djstripe',
    'drf_multiple_model',
    'django_celery_beat',
    'import_export',
    'phonenumber_field',
    'constance',
    'constance.backends.database',
    'fcm_django',
    'ckeditor',
    'ckeditor_uploader',
    'admin_auto_filters',
    'crispy_forms',
    'rest_framework_tracking',
    'easyaudit',
    'django_admin_logs',
)

SITE_ID = 1

LOCAL_APPS = (
    'libs',
    # Our custom admin app (to add dashboard to index page)
    'apps.admin',
    'apps.users',
    'apps.business',
    'apps.forums',
    'apps.finance',
    'apps.notifications',
    'apps.promotion',
    'apps.documents',
    'apps.esign',
    'apps.news',
    'apps.social',
    'apps.accounting',
)

INSTALLED_APPS += LOCAL_APPS + HEALTH_CHECKS_APPS
