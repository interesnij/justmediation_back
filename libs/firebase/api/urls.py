from rest_framework import routers
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from . import views


router = routers.SimpleRouter()

router.register(
    r'',
    views.FirestoreCredentialsView,
    basename='firestore-credentials'
)
router.register('devices', FCMDeviceAuthorizedViewSet)


urlpatterns = router.urls
