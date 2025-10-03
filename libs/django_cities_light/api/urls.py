from rest_framework.routers import DefaultRouter
from ..api import views


app_name = 'locations'

router = DefaultRouter()
router.register(r'top-cities', views.TopCityViewSet, basename='top-cities')
router.register(r'cities', views.CityViewSet, basename='cities')
router.register(r'states', views.RegionsViewSet, basename='regions')
router.register(r'countries', views.CountryViewSet, basename='countries')

urlpatterns = router.urls
