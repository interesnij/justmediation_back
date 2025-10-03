from django.conf import settings
from django.conf.urls import include
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic.base import RedirectView

from libs.views import main_page

from .admin import urlpatterns as admin_urlpatterns
from .api_versions import urlpatterns as api_urlpatterns
from .debug import urlpatterns as debug_urlpatterns
from .swagger import urlpatterns as swagger_urlpatterns

urlpatterns = [
    path('', main_page.IndexView.as_view(), name='index'),
    path(
        'health-check',
        main_page.HealthCheckView.as_view(),
        name='health-check'
    ),
    path(
        'favicon.png',
        RedirectView.as_view(url=staticfiles_storage.url('favicon.png')),
        name="favicon"
    ),
    path('users/', include('apps.users.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += admin_urlpatterns
urlpatterns += api_urlpatterns
urlpatterns += debug_urlpatterns

# add swagger urls only to not production envs
if settings.ENVIRONMENT != 'production':
    urlpatterns += swagger_urlpatterns
