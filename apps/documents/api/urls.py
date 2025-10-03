from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(
    r'',
    views.ResourcesView,
    basename='resources'
)
router.register(
    r'folders',
    views.FolderViewSet,
    basename='folders'
)
router.register(
    r'documents',
    views.DocumentViewSet,
    basename='documents'
)

urlpatterns = [
    path(r'', include(router.urls))
]
