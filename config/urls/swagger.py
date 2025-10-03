from django.conf import settings
from django.urls import path, re_path

from rest_framework import permissions

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(**settings.API_INFO_BACKEND),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Swagger urls
urlpatterns = [
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    path(
        'swagger',
        schema_view.with_ui(
            'swagger',
            cache_timeout=0,
        ),
        name='schema-swagger-ui',
    ),
]
