from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from authentication import apis

urlpatterns = [
    path('register/', apis.UserRegisterAPI.as_view(), name='register'),
    path('login/', apis.UserLoginAPI.as_view(), name='login'),
    path('me/', apis.UserMeAPI.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
