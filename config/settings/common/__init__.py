# -----------------------------------------------------------------------------
# General Django Configuration Starts Here
# -----------------------------------------------------------------------------

from .allauth import *
from .authentication import *
from .cacheops import *
from .celery import *
from .cities import *
from .ckeditor import *
from .constance import *
from .cors import *
from .django_easy_audit import *
from .docusign import *
from .drf import *
from .firebase import *
from .general import *
from .gis import *
from .health_check import *
from .imagekit import *
from .installed_apps import *
from .internationalization import *
from .logging import *
from .middleware import *
from .notifications import *
from .paths import *
from .quickbooks import *
from .static import *
from .stripe import *
from .swagger import *
from .templates import *

SITE_ID = 1
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TESTING = os.environ.get('PYTEST_TESTING', False)
