from rest_framework.routers import DefaultRouter

from ..api import views

router = DefaultRouter()
router.register(
    r'',
    views.NotificationDispatchViewSet,
    basename='notifications'
)
router.register(
    r'settings',
    views.NotificationSettingViewSet,
    basename='notifications_settings'
)
router.register(
    r'types',
    views.NotificationTypeViewSet,
    basename='notifications_types'
)
router.register(
    r'groups',
    views.NotificationGroupViewSet,
    basename='notifications_groups'
)

urlpatterns = router.urls
