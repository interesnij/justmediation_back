from django.urls import include, path

app_name = 'api'

# API endpoints
urlpatterns = [
    # Apps' apis
    path('', include('apps.users.api.urls')),
    path('documents/', include('apps.documents.api.urls')),
    path('business/', include('apps.business.api.urls')),
    path('promotion/', include('apps.promotion.api.urls')),
    path('forum/', include('apps.forums.api.urls')),
    path('notifications/', include('apps.notifications.api.urls')),
    path('finance/', include('apps.finance.api.urls')),
    path('esign/', include('apps.esign.api.urls')),
    path('news/', include('apps.news.api.urls')),
    path('accounting/', include('apps.accounting.api.urls')),
    path('social/', include('apps.social.api.urls')),
    # Utils' apis
    path('fcm', include('apps.utils.fcm.urls')),
    # Libs' apis
    path('firestore/', include('libs.firebase.api.urls')),
    path('locations/', include('libs.django_cities_light.api.urls')),
    path('utils/health-check/', include('libs.health_checks.api.urls')),
]

