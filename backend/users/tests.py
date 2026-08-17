from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    Language,
)
from unittest.mock import patch
from django.test import TestCase
from .services import (
    send_email_verification_email,
    send_password_reset_email,
)

from .serializers import (
    UserRegistrationSerializer,
    EmailVerificationTokenSerializer,
    PasswordResetTokenSerializer,
    
)

User = get_user_model()

class UserLoginAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPass123",
            email_verified=True,
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

    def test_update_profile(self):
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

    def test_unverified_email_cannot_login(self):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "loginuser",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )

        self.assertEqual(
            response.data["email"][0],
            "Please verify your email address before logging in.",
        )

        self.assertNotIn(
            "access",
            response.data,
        )

        self.assertNotIn(
            "refresh",
            response.data,
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

    @patch("users.views.send_email_verification_email")
    def test_registration_sends_verification_email(self, mock_send_email):
        data = {
            "username": "emailtestuser",
            "email": "emailtest@example.com",
            "password": "StrongPass123",
            "first_name": "Email",
            "last_name": "Test",
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

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user.email,
            "emailtest@example.com",
        )

        self.assertEqual(
            called_token.user,
            called_user,
        )

        self.assertFalse(
            called_token.used,
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

class ResendVerificationAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resenduser",
            email="resend@example.com",
            password="StrongPass123",
            email_verified=False,
        )

    @patch("users.views.send_email_verification_email")
    def test_resend_verification_sends_email(
        self,
        mock_send_email,
    ):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a verification email has been sent."
            ),
        )

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user,
            self.user,
        )

        self.assertEqual(
            called_token.user,
            self.user,
        )

        self.assertFalse(
            called_token.used,
        ) 

    def test_resend_verification_invalidates_old_token(self):
        token_serializer = EmailVerificationTokenSerializer()

        old_token = token_serializer.create_token(self.user)

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        old_token.refresh_from_db()

        self.assertTrue(
            old_token.used,
        )

        self.assertEqual(
            PasswordResetToken.objects.filter(
                user=self.user,
            ).count(),
            0,
        )

        self.assertEqual(
            EmailVerificationToken.objects.filter(
                user=self.user,
                used=False,
            ).count(),
            1,
        )

    def test_resend_verification_unknown_email(self):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "unknown@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a verification email has been sent."
            ),
        )

    def test_resend_verification_already_verified(self):
        self.user.email_verified = True
        self.user.save(
            update_fields=["email_verified"],
        )

        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "resend@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )

        self.assertEqual(
            response.data["email"][0],
            "Email address is already verified.",
        )

    def test_resend_verification_invalid_email(self):
        response = self.client.post(
            "/api/auth/resend-verification/",
            {
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )                   

class PasswordResetTokenTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="StrongPass123",
        )

    def test_password_reset_token_is_created(self):
        serializer = PasswordResetTokenSerializer()

        token = serializer.create_token(self.user)

        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.used)
        self.assertFalse(token.is_expired())

    def test_old_reset_token_are_invalidated(self):
        serializer = PasswordResetTokenSerializer()

        first_token = serializer.create_token(self.user)
        second_token = serializer.create_token(self.user)

        first_token.refresh_from_db()

        self.assertTrue(first_token.used)
        self.assertFalse(second_token.used)

    def test_reset_token_expires(self):
        serializer =PasswordResetTokenSerializer()

        token = serializer.create_token(self.user)

        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save(update_fields=["expires_at"])

        self.assertTrue(token.is_expired())

class ForgotPasswordAPItestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="forgotuser",
            email="forgot@example.com",
            password="StrongPass123",
        )

    def test_forgot_password_existing_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "forgot@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a password reset link has been sent."
            ),
        )

        self.assertTrue(
            PasswordResetToken.objects.filter(
                user=self.user,
                used=False,
            ).exists()
        )
    @patch("users.views.send_password_reset_email")
    def test_forgot_password_sends_reset_email(self, mock_send_email):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "forgot@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_send_email.assert_called_once()

        called_user = mock_send_email.call_args.args[0]
        called_token = mock_send_email.call_args.args[1]

        self.assertEqual(
            called_user,
            self.user,
        )

        self.assertEqual(
            called_token.user,
            self.user,
        )

        self.assertFalse(
            called_token.used,
        ) 

       
    def test_forgot_password_unknow_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "unknow@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            (
                "If an account exists with this email, "
                "a password reset link has been sent."
            ),
        )

    def test_forgot_password_invalid_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )       

class ResetPasswordAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetapiuser",
            email="resetapi@example.com",
            password="OldPassword123",
        )

        serializer = PasswordResetTokenSerializer()
        self.token = serializer.create_token(self.user)

    def test_reset_password_success(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            "Password reset successfully.",
        )

        self.user.refresh_from_db()
        self.token.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword123")
        )

        self.assertTrue(self.token.used)

    def test_invalid_reset_token_is_rejected(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": "550e8400-e29b-41d4-a716-446655440000",
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_used_reset_token_is_rejected(self):
        self.token.used = True
        self.token.save(update_fields=["used"])

        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_expired_reset_token_is_rejected(self):
        self.token.expires_at = timezone.now() - timedelta(minutes=1)
        self.token.save(update_fields=["expires_at"])

        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
                "new_password": "NewPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_new_password_is_required(self):
        response = self.client.post(
            "/api/auth/reset-password/",
            {
                "token": str(self.token.token),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

class EmailServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="emailserviceuser",
            email="emailservice@example.com",
            password="StrongPass123",
        )

    @patch("users.services.send_mail")
    def test_send_email_verification_email(self, mock_send_mail):
        serializer = EmailVerificationTokenSerializer()
        token = serializer.create_token(self.user)

        send_email_verification_email(
            self.user,
            token,
        )

        mock_send_mail.assert_called_once()

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertEqual(
            call_kwargs["subject"],
            "Verify your email",
        )

        self.assertEqual(
            call_kwargs["recipient_list"],
            ["emailservice@example.com"],
        )

        self.assertIn(
            str(token.token),
            call_kwargs["message"],
        )

    @patch("users.services.send_mail")
    def test_send_password_reset_email(self, mock_send_mail):
        serializer = PasswordResetTokenSerializer()
        token = serializer.create_token(self.user)

        send_password_reset_email(
            self.user,
            token,
        )

        mock_send_mail.assert_called_once()

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertEqual(
            call_kwargs["subject"],
            "Reset your password",
        )

        self.assertEqual(
            call_kwargs["recipient_list"],
            ["emailservice@example.com"],
        )

        self.assertIn(
            str(token.token),
            call_kwargs["message"],
        )

class LanguageListAPITestCase(APITestCase):
    def setUp(self):
        self.active_language = Language.objects.create(
            name="Test English",
            code="test-en",
            native_name="Test English",
            is_active=True,
        )

        self.second_active_language = Language.objects.create(
            name="Test Hindi",
            code='test-hi',
            native_name="परीक्षण हिन्दी",
            is_active=True,
        )

        self.inactive_language = Language.objects.create(
            name="Test French",
            code="test-fr",
            native_name="Test Francias",
            is_active=False,      
        )

    def test_language_list_returns_active_languages(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_codes = [
            language["code"]
            for language in response.data
        ]

        self.assertIn(
            "test-en",
            returned_codes,
        )

        self.assertIn(
            "test-hi",
            returned_codes,
        )

        self.assertNotIn(
            "test-fr",
            returned_codes,
        )

    def test_inactive_language_is_not_returned(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_codes = [
            language["code"]
            for language in response.data
        ]

        self.assertNotIn(
            "test-fr",
            returned_codes,
        )

    def test_language_list_is_ordered_by_name(self):
        response = self.client.get(
            "/api/auth/languages/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        names = [
            language["name"]
            for language in response.data
        ]

        self.assertEqual(
            names,
            sorted(names),
        )            