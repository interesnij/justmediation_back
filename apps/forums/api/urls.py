from rest_framework import routers

from apps.forums.api import views

router = routers.DefaultRouter()

router.register(
    'topics',
    views.TopicViewSet,
    basename='topics',
)

router.register(
    'posts',
    views.PostViewSet,
    basename='posts',
)

router.register(
    'comments',
    views.CommentViewSet,
    basename='comments',
)

router.register(
    'followed',
    views.FollowedPostViewSet,
    basename='followed',
)
router.register(
    'followed_topics',
    views.FollowedTopicViewSet,
    basename='followed',
)
router.register(
    'practice_areas',
    views.PracticeAreaViewSet,
    basename='practice_areas',
)

urlpatterns = router.urls
