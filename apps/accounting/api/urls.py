from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(
    r'auth',
    views.QuickBooksAuthorizationView,
    basename='quickbooks-auth'
)

router.register(
    r'export',
    views.QuickBooksExportView,
    basename='quickbooks-export'
)

urlpatterns = router.urls
