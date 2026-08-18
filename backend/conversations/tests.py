from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation

User = get_user_model()

class ConversationModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="conversationuser",
            email="conversation@example.com",
            password="StrongPass123",
        )

    def test_create_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="My First Conversation",
        )

        self.assertEqual(
            conversation.user,
            self.user,
        )

        self.assertEqual(
            conversation.title,
            "My First Conversation",
        )

        self.assertFalse(
            conversation.is_archived,
        ) 

        self.assertIsNotNone(
            conversation.created_at,
        ) 

    def test_conversation_string_representation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation",
        )

        self.assertEqual(
            str(conversation),
            "Test Conversation",
        )

    def test_user_can_have_multiple_conversations(self):
        Conversation.objects.create(
            user=self.user,
            title="Conversation One",
        )

        Conversation.objects.create(
            user=self.user,
            title="Conversation Two",
        )

        self.assertEqual(
            self.user.conversations.count(),
            2,
        )

class ConversationAPItestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@example.com",
            password="StrongPass123",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPass123",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_create_conversation(self):
        response = self.client.post(
            "/api/conversations/",
            {
                "title": "My First Conversation",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["title"],
            "My First Conversation",
        )

        self.assertTrue(
            Conversation.objects.filter(
                user=self.user,
                title="My First Conversation",
            ).exists()
        )

    def test_list_only_own_conversations(self):
        Conversation.objects.create(
            user=self.user,
            title="My Conversation",
        )

        Conversation.objects.create(
            user=self.other_user,
            title="Other User Conversation",
        )

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["title"],
            "My Conversation",
        )

    def test_retrieve_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="My Conversation",
        )

        response = self.client.get(
            f"/api/conversations/{conversation.id}/"
        ) 

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["title"],
            "My Conversation",
        )

    def test_cannot_retrieve_other_users_conversation(self):
        conversation = Conversation.objects.create(
            user=self.other_user,
            title="Private Conversation",
        )

        response = self.client.get(
            f"/api/conversations/{conversation.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_update_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Old Title",
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "title": "Updated Title",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "Updated Title",
        )

    def test_delete_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Delete Me",
        )

        response = self.client.delete(
            f"/api/conversations/{conversation.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Conversation.objects.filter(
                id=conversation.id
            ).exists()
        )

    def test_unauthenticated_user_cannot_access_conversations(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )                           