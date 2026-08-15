from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.utils import timezone

from .serializers import (
    UserRegistrationSerializer,
    EmailVerificationTokenSerializer,
)

User = get_user_model()

class UserLoginAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123",
        )

    def test_user_login_return_tokens(self):
        data = {
            "username": "loginuser",
            "password": "StrongPass123",
        }

        response = self.client.post(
            "/api/auth/login/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])

    def test_invallid_password_is_rejected(self):
        data = {
            "username": "loginuser",
            "password": "WrongPassword123",
        }

        response = self.client.post(
            "/api/auth/login/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_token_return_new_access_token(self):
        login_data = {
            "username": "loginuser",
            "password": "StrongPass123",
        }

        login_response = self.client.post(
            "/api/auth/login/",
            login_data, format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        refresh_token = login_response.data["refresh"]
        response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertTrue(response.data["access"])

    def test_current_user_requires_authentication(self):
        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_return_authenticated_user(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format='json',
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "loginuser",
        )

        self.assertEqual(
            response.data["email"],
            "login@example.com",
        )

    def test_logout_blacklist_refresh_token(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        logout_response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            logout_response.data["message"],
            "Successfully logged out.",
        )

        refresh_response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_requires_authentication(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            "/api/auth/logout/",
            {
                "refresh": refresh_token,
            },
            format ="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            "/api/auth/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_profile_returns_authentication_user(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            fromat="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/profile/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "loginuser",
        )

        self.assertEqual(
            response.data["email"],
            "login@example.com",
        )

    def test_ipdate_profile(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.patch(
            "/api/auth/profile/",
            {
                "first_name": "Updated",
                "last_name": "User",
                "preferred_language": "Englis",
                "voice_language": "Hindi",
                "timezone": "Asia/Kolkata",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["first_name"],
            "Updated",
        )

        self.assertEqual(
            response.data["voice_language"],
            "Hindi",
        )

        self.assertEqual(
            response.data["timezone"],
            "Asia/Kolkata",
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertEqual(
            user.first_name,
            "Updated",
        )

        self.assertEqual(
            user.voice_language,
            "Hindi",
        )

    def test_profile_cannot_update_username_or_email(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.patch(
            "/api/auth/profile/",
            {
                "username": "changed_username",
                "email": "changed@example.com",
                "first_name": "Protected",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertEqual(
            user.username,
            "loginuser",
        )

        self.assertEqual(
            user.email,
            "login@example.com",
        )

        self.assertEqual(
            user.first_name,
            "Protected",
        )

    def test_change_password_requires_authentication(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_change_password_success(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            "Password changed successfully.",
        )

        user = User.objects.get(
            username="loginuser"
        )

        self.assertTrue(
            user.check_password("NewStrongPass456")
        )

        self.assertFalse(
            user.check_password("StrongPass123")
        )

    def test_change_password_rejects_wrong_old_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "WrongPassword123",
                "new_password": "NewStrongPass456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "old_password", response.data,
        )

    def test_change_password_rejects_same_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password", response.data,
        )

    def test_change_password_rejects_short_password(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )
        access_token = login_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "StrongPass123",
                "new_password": "123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password", response.data,
        )


class UserRegistrationSerializerTestCase(APITestCase):
    def test_valid_user_registration(self):
        data = {
            "username": "sahil",
            "email": "sahil@786.com",
            "password": "StrongPass123",
            "first_name": "Sahil",
            "last_name": "Siddiquie",
            "preferred_language": "English",
            "voice_language": "Hindi",
            "timezone": "Asia/KolKata",
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "sahil@786.com")
        self.assertEqual(user.first_name, "Sahil")
        self.assertEqual(user.preferred_language, "English")

        # Password must be stored as plain text.
        self.assertNotEqual(user.password, "StrongPass123")

        # Django should be able to verify the password.
        self.assertTrue(user.check_password("StrongPass123"))

    def test_short_password_is_rejected(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

class UserRegistrationAPITestCase(APITestCase):
    def test_user_registration_api(self):
        data = {
            "username": "apiuser",
            "email": "apiuser@example.com",
            "password": "StrongPass123",
            "first_name": "API",
            "last_name": "User",
            "preferred_language": "English",
            "voice_language": "Hindi",
            "timezone": "Asia/Kolkata",
        }

        response = self.client.post(
            "/api/auth/register/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["message"],
            "User registered successfully.",
        )

        self.assertEqual(
            response.data["user"]["email"],
            "apiuser@example.com",
        )

        self.assertTrue(
            User.objects.filter(
                email="apiuser@example.com"
            ).exists()
        )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123",
        )

        data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "StrongPass123",
        } 

        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("email", response.data)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123",
        )

        data = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "StrongPass123",
        }

        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("username", response.data)

    def test_missing_email_is_rejected(self):
        data = {
            "username": "missingemail",
            "password": "StrongPass123",
        } 
        response = self.client.post(
            "/api/auth/register/",
            data, format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn("email", response.data) 

class EmailVerificationTokenTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="verificationuser",
            email="verification@example.com",
            password="StrongPass123",
        )

    def test_verification_token_is_created(self):
        serializer = EmailVerificationTokenSerializer()

        token = serializer.create_token(self.user)

        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        self.assertFalse(token.is_expired())

    def test_old_unused_tokens_are_invalidated(self):
        serializer = EmailVerificationTokenSerializer()

        first_token = serializer.create_token(self.user)
        second_token = serializer.create_token(self.user)

        first_token.refresh_from_db()

        self.assertTrue(first_token.used)
        self.assertFalse(second_token.used)

    def test_token_expires_after_expiration_time(self):
        serializer = EmailVerificationTokenSerializer()

        token = serializer.create_token(self.user)

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        self.assertTrue(token.is_expired())    

class EmailVerificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="verifyuser",
            email="verify@example.com",
            password="StrongPass123",
        )

    def create_token(self):
        serializer = EmailVerificationTokenSerializer()
        return serializer.create_token(self.user)

    def test_valid_token_verifies_email(self):
        token = self.create_token()

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()
        token.refresh_from_db()

        self.assertTrue(self.user.email_verified)
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertTrue(token.used)

        self.assertEqual(
            response.data["message"],
            "Email verified successfully.",
        )

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": "550e8400-e29b-41d4-a716-446655440000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_expired_token_is_rejected(self):
        token = self.create_token()

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.user.refresh_from_db()
        token.refresh_from_db()

        self.assertFalse(self.user.email_verified)
        self.assertFalse(token.used)

    def test_used_token_is_rejected(self):
        token = self.create_token()

        token.used= True
        token.save(update_fields=["used"])

        response = self.client.post(
            "/api/auth/verify-email/",
            {
                "token": str(token.token),
            },
            fromat="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )                