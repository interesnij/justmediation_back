from django.urls import re_path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(
    r'envelopes',
    views.EnvelopeViewSet,
    basename='envelope'
)

router.register(
    r'callbacks',
    views.ESignCallbacksView,
    basename='callbacks'
)

urlpatterns = router.urls
urlpatterns += [
    re_path(
            r'^profiles/current/$',
            views.CurrentESignProfileView.as_view(),
            name='current_esign_profile'
        ),
]
