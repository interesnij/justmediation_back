from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import FCMViewSet

fcm_router = DefaultRouter()

fcm_router.register('devices', FCMViewSet)

urlpatterns = (
    path('', include(fcm_router.urls)),
)
