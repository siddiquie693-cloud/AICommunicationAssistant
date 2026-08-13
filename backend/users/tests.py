from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .serializers import UserRegistrationSerializer

User = get_user_model()

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