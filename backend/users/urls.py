from django.urls import path
from rest_framework_simplejwt.views import ( 
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    LogoutAPIView,
    UserRegistrationAPIVIew,
    CurentUserAPIVIew,
    UserProfileAPIView,
)

urlpatterns = [
    path("register/", UserRegistrationAPIVIew.as_view(), name="user-register",),
    path("login/", TokenObtainPairView.as_view(), name="token-obtain-pair",),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh",),
    path("me/", CurentUserAPIVIew.as_view(), name="current-user",),
    path("logout/", LogoutAPIView.as_view(), name="logout",),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile",),
]