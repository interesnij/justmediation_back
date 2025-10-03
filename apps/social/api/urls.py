from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()

router.register(
    r'chats',
    views.ChatViewSet,
    basename='chats',
)

router.register(
    r'posts',
    views.MediatorPostViewSet,
    basename='mediator_posts',
)

urlpatterns = [
    path(r'', include(router.urls))
]
