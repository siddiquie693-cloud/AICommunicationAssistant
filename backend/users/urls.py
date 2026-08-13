from django.urls import path
from rest_framework_simplejwt.views import ( 
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    UserRegistrationAPIVIew,
    CurentUserAPIVIew,
)

urlpatterns = [
    path("register/", UserRegistrationAPIVIew.as_view(), name="user-register",),
    path("login/", TokenObtainPairView.as_view(), name="token-obtain-pair",),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh",),
    path("me/", CurentUserAPIVIew.as_view(), name="current-user",),
]