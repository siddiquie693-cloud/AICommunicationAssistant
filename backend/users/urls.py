from django.urls import path
from .views import UserRegistrationAPIVIew

urlpatterns = [
    path("register/", UserRegistrationAPIVIew.as_view(), name="user-register",),
]