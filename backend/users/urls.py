from django.urls import path
from rest_framework_simplejwt.views import ( 
    TokenRefreshView,
)

from .views import (
    LogoutAPIView,
    UserRegistrationAPIVIew,
    CurentUserAPIVIew,
    UserProfileAPIView,
    ChangePasswordAPIView,
    EmailVerificationAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
    UserLoginAPIView,
    ResendVerificationAPIView,
)

urlpatterns = [
    path("register/", UserRegistrationAPIVIew.as_view(), name="user-register",),
    path("login/", UserLoginAPIView.as_view(), name="token-obtain-pair",),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh",),
    path("me/", CurentUserAPIVIew.as_view(), name="current-user",),
    path("logout/", LogoutAPIView.as_view(), name="logout",),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile",),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password",),
    path("verify-email/", EmailVerificationAPIView.as_view(), name="verify-email",),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password",),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password",),
    path("resend-verification/", ResendVerificationAPIView.as_view(), name="resend-verification",),
]