from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(
    '',
    views.NewsViewSet,
    basename='news',
)

router.register(
    'categories',
    views.NewsCategoryViewSet,
    basename='news-categories',
)

router.register(
    'tags',
    views.NewsTagViewSet,
    basename='news-tags',
)

urlpatterns = router.urls
