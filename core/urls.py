from django.urls import path
from core import apis

urlpatterns = [
    path("health/", apis.HealthCheckAPI.as_view(), name="health"),
]
