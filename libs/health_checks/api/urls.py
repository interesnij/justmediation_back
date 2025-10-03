from django.urls import path
from ..api import views


app_name = 'health_check'

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health_check'),
]
