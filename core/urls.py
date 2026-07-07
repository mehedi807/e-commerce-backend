from django.urls import path
from core.apis import HealthCheckAPI

urlpatterns = [
    path("health/", HealthCheckAPI.as_view(), name="health"),
]
