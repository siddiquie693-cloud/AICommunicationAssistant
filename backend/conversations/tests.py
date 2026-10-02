from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from ai.text_to_speech.exceptions import TextToSpeechProviderError
from users.models import NIRAPersonalProfile
from conversations.services.ai_conversation_service import (
    AIConversationService,
)

from .models import Conversation, Message
from django.utils import timezone

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
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "My Conversation",
        )

    def test_conversation_list_is_paginated(self):
        for index in range(15):
            Conversation.objects.create(
                user=self.user,
                title=f"Conversation {index}",
            )

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            15,
        )

        self.assertEqual(
            len(response.data["results"]),
            10,
        )

        self.assertIsNotNone(
            response.data["next"]
        )

    def test_conversation_page_size_can_be_changed(self):
        for index in range(15):
            Conversation.objects.create(
                user=self.user,
                title=f"Conversation {index}",
            )
        response = self.client.get(
            "/api/conversations/?page_size=5"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            15,
        )

        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_conversation_page_size_cannot_exceed_maximum(self):
        for index in range(60):
            Conversation.objects.create(
                user=self.user,
                title=f"Conversation {index}",
            )
        response = self.client.get(
            "/api/conversations/?page_size=100"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            60,
        )

        self.assertEqual(
            len(response.data["results"]),
            50,
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

    def test_create_conversation_rejects_empty_title(self):
        response = self.client.post(
            "/api/conversations/",
            {
                "title": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Conversation.objects.filter(
                user=self.user,
                title="",
            ).exists()
        )

    def test_create_conversation_rejects_whitespace_title(self):
        response = self.client.post(
            "/api/conversations/",
            {
                "title": "  ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_conversation_strips_title_whitespace(self):
        response = self.client.post(
            "/api/conversations/",
            {
                "title": " My Conversation ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["title"],
            "My Conversation",
        )

        self.assertTrue(
            Conversation.objects.filter(
                user=self.user,
                title="My Conversation",
            ).exists()
        )

    def test_update_conversation_rejects_empty_title(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Original Title",
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "title": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "Original Title",
        )

    def test_update_conversation_rejects_whitespace_title(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Original Title",
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "title": "  ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        conversation.refresh_from_db()

        self.assertEqual(
            conversation.title,
            "Original Title",
        )

    def test_update_conversation_strips_title_whitespace(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Original Title",
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "title": " Updated Title ",
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

        self.assertEqual(
            response.data["title"],
            "Updated Title",
        )

    def test_delete_own_conversation_soft_deletes(self):
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

        conversation.refresh_from_db()

        self.assertIsNotNone(
            conversation.deleted_at
        )

    def test_deleted_conversation_is_excluded_from_list(self):
        Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
        )

        deleted_conversation = Conversation.objects.create(
            user=self.user,
            title="Deleted Conversation",
        )

        deleted_conversation.deleted_at = timezone.now()
        deleted_conversation.save()

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Active Conversation",
        )

    def test_restore_deleted_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Restore Me",
            deleted_at=timezone.now(),
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/restore/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        conversation.refresh_from_db()

        self.assertIsNone(
            conversation.deleted_at,
        )

        self.assertEqual(
            response.data["id"],
            conversation.id,
        )

        self.assertEqual(
            response.data["title"],
            "Restore Me",
        )

    def test_restored_conversation_appears_in_list(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Restore and List",
            deleted_at=timezone.now(),
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/restore/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        list_response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            list_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            list_response.data["count"],
            1,
        )

        self.assertEqual(
            list_response.data["results"][0]["id"],
            conversation.id,
        )

    def test_restore_active_conversation_is_rejected(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Already Active",
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/restore/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_restore_other_users_deleted_conversation(self):
        conversation = Conversation.objects.create(
            user=self.other_user,
            title="Private Deleted Conversation",
            deleted_at=timezone.now(),
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/restore/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        conversation.refresh_from_db()

        self.assertIsNotNone(
            conversation.deleted_at,
        )

    def test_list_deleted_conversation_in_trash(self):
        Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
        )

        deleted_conversation = Conversation.objects.create(
            user=self.user,
            title="Deleted Conversation",
            deleted_at=timezone.now(),
        )

        response = self.client.get(
            "/api/conversations/trash/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            deleted_conversation.id,
        )

    def test_trash_excludes_active_conversations(self):
        active_conversation = Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
        )

        response = self.client.get(
            "/api/conversations/trash/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertNotIn(
            active_conversation.id,
            [
                item["id"]
                for item in response.data["results"]
            ],
        )

    def test_trash_excludes_other_users_deleted_conversations(self):
        Conversation.objects.create(
            user=self.other_user,
            title="Other User Deleted",
            deleted_at=timezone.now(),
        )

        response = self.client.get(
            "/api/conversations/trash/"
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

    def test_search_deleted_conversations_in_trash(self):
        Conversation.objects.create(
            user=self.user,
            title="Deleted Python Project",
            deleted_at=timezone.now(),
        )

        Conversation.objects.create(
            user=self.user,
            title="Deleted Java Project",
            deleted_at=timezone.now(),
        )

        response = self.client.get(
            "/api/conversations/trash/?search=Python"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Deleted Python Project",
        )

    def test_empty_trash_returns_empty_results(self):
        response = self.client.get(
            "/api/conversations/trash/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertEqual(
            len(response.data["results"]),
            0,
        )

    def test_restored_conversation_is_removed_from_trash(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Restore From Trash",
            deleted_at=timezone.now(),
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/restore/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        trash_response = self.client.get(
            "/api/conversations/trash/"
        )

        self.assertEqual(
            trash_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            trash_response.data["count"],
            0,
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

    def test_archive_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Archive Me",
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "is_archived": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        conversation.refresh_from_db()

        self.assertTrue(
            conversation.is_archived
        )

        self.assertTrue(
            response.data["is_archived"]
        )

    def test_unarchive_own_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Unarchive Me",
            is_archived=True,
        )

        response = self.client.patch(
            f"/api/conversations/{conversation.id}/",
            {
                "is_archived": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        conversation.refresh_from_db()

        self.assertFalse(
            conversation.is_archived
        )

        self.assertFalse(
            response.data["is_archived"]
        )

    def test_list_excludes_archived_conversations_by_default(self):
        Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
            is_archived=False,
        )

        Conversation.objects.create(
            user=self.user,
            title="Archived Conversation",
            is_archived=True,
        )

        response = self.client.get(
            "/api/conversations/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Active Conversation",
        )

    def test_list_archived_conversations(self):
        Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
            is_archived=False,
        )

        Conversation.objects.create(
            user=self.user,
            title="Archived Conversation",
            is_archived=True,
        )

        response = self.client.get(
            "/api/conversations/?archived=true"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Archived Conversation",
        )

    def test_list_active_conversations(self):
        Conversation.objects.create(
            user=self.user,
            title="Active Conversation",
            is_archived=False,
        )

        Conversation.objects.create(
            user=self.user,
            title="Archived Conversation",
            is_archived=True,
        )

        response = self.client.get(
            "/api/conversations/?archived=false"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Active Conversation",
        )

    def test_search_conversations_by_title(self):
        Conversation.objects.create(
            user=self.user,
            title="Python Backend Project",
        )

        Conversation.objects.create(
            user=self.user,
            title="AI Communication Assistant",
        )

        response = self.client.get(
            "/api/conversations/?search=Python"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Python Backend Project",
        )

    def test_search_conversations_is_case_insensitive(self):
        Conversation.objects.create(
            user=self.user,
            title="Python Backend Project",
        )

        response = self.client.get(
            "/api/conversations/?search=python"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Python Backend Project",
        )

    def test_search_conversations_returns_empty_when_no_match(self):
        Conversation.objects.create(
            user=self.user,
            title="Python Backend Project",
        )

        response = self.client.get(
            "/api/conversations/?search=Java"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertEqual(
            len(response.data["results"]),
            0,
        )

    def test_conversation_list_can_order_oldest_first(self):
        first = Conversation.objects.create(
            user=self.user,
            title="First Conversation",
        )

        second = Conversation.objects.create(
            user=self.user,
            title="Second Conversation",
        )

        response = self.client.get(
            "/api/conversations/?ordering=created_at"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            first.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            second.id,
        )

    def test_conversation_list_can_order_newest_first(self):
        first = Conversation.objects.create(
            user=self.user,
            title="First Conversation",
        )

        second = Conversation.objects.create(
            user=self.user,
            title="Second Conversation",
        )

        response = self.client.get(
            "/api/conversations/?ordering=-created_at"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            second.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            first.id,
        )

    def test_invalid_conversation_ordering_defaults_to_newest(self):
        first = Conversation.objects.create(
            user=self.user,
            title="First Conversation",
        )

        second = Conversation.objects.create(
            user=self.user,
            title="Second Conversation",
        )

        response = self.client.get(
            "/api/conversations/?ordering=invalid"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            second.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            first.id,
        )

class MessageListCreateAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="messageuser",
            email="messageuser@example.com",
            password="StrongPass123",
        )
        self.generate_response_patcher = patch(
            "conversations.views.AIConversationService.generate_response"
        )
        self.mock_generate_response = (
            self.generate_response_patcher.start()
        )

        self.other_user = User.objects.create_user(
            username="othermessageuser",
            email="othermessageuser@example.com",
            password="StrongPass123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Message Test Conversation",
        )

        self.other_conversation = Conversation.objects.create(
            user=self.other_user,
            title="Other User Conversation",
        )

        self.client.force_authenticate(
            user=self.user
        )
        self.addCleanup(
            self.generate_response_patcher.stop
        )
        
    @patch(
        "conversations.views.AIConversationService.generate_response"
    )
    def test_ai_response_generation_is_mocked(
        self,
        mock_generate_response,
    ):
        mock_generate_response.return_value = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Mock AI response",
        )   

    def test_list_messages(self):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hello",
        )

        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Hi! How can I help?",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

        self.assertEqual(
            response.data["results"][0]["content"],
            "Hello",
        )

        self.assertEqual(
            response.data["results"][1]["sender_type"],
            Message.SENDER_ASSISTANT,
        )

    def test_message_list_is_paginated(self):
        for index in range(15):
            Message.objects.create(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
                content=f"Message {index}",
            )
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            15,
        )

        self.assertEqual(
            len(response.data["results"]),
            10,
        )

        self.assertIsNotNone(
            response.data["next"]
        )

    def test_message_page_size_can_be_changed(self):
        for index in range(15):
            Message.objects.create(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
                content=f"Message {index}",
            )
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?page_size=5"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            15,
        )

        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_message_page_size_cannot_exceed_maximum(self):
        for index in range(60):
            Message.objects.create(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
                content=f"Message {index}",
            )
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?page_size=100"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            60,
        )

        self.assertEqual(
            len(response.data["results"]),
            50,
        )

    def test_search_messages_by_content(self):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hello, how are you?",
        )

        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Tell me about Python.",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?search=Python"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["content"],
            "Tell me about Python.",
        )

    def test_search_messages_is_case_insensitive(self):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hello Python Developer",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?search=python"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["content"],
            "Hello Python Developer",
        )

    def test_search_messages_returns_empty_when_no_match(self):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hello, how are you?",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?search=Java"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            0,
        )

        self.assertEqual(
            len(response.data["results"]),
            0,
        )

    def test_create_user_message(self):
        data = {
            "sender_type": Message.SENDER_USER,
            "content": "Hello, I need help.",
        }

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["sender_type"],
            Message.SENDER_USER,
        )

        self.assertEqual(
            response.data["content"],
            "Hello, I need help.",
        )

        self.assertTrue(
            Message.objects.filter(
                conversation=self.conversation,
                content="Hello, I need help.",
            ).exists()
        )

    def test_create_message_rejects_empty_content(self):
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            {
                "sender_type": Message.SENDER_USER,
                "content": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_message_rejects_whitespace_content(self):
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            {
                "sender_type": Message.SENDER_USER,
                "content": "  ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_message_strips_content_whitespace(self):
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            {
                "sender_type": Message.SENDER_USER,
                "content": " Hello Python ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["content"],
            "Hello Python",
        )

        self.assertTrue(
            Message.objects.filter(
                conversation=self.conversation,
                content="Hello Python",
            ).exists()
        )

    def test_update_message_strips_content_whitespace(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Original Message",
        )

        response = self.client.patch(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/",
            {
                "content": " Updated Message ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        message.refresh_from_db()

        self.assertEqual(
            message.content,
            "Updated Message",
        )

        self.assertEqual(
            response.data["content"],
            "Updated Message",
        )

    def test_update_message_rejects_empty_content(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Original Message",
        )

        response = self.client.patch(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/",
            {
                "content": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        message.refresh_from_db()

        self.assertEqual(
            message.content,
            "Original Message",
        )

    def test_create_message_rejects_invalid_sender_type(self):
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            {
                "sender_type": "invalid",
                "content": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_message_are_inaccessible_for_deleted_conversation(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hidden message",
        )

        self.conversation.deleted_at = timezone.now()
        self.conversation.save(
            update_fields=["deleted_at"]
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Message.objects.filter(
                id=message.id
            ).exists()
        )

    def test_individual_message_is_inaccessible_for_deleted_conversation(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hidden individual message",
        )

        self.conversation.deleted_at = timezone.now()
        self.conversation.save(
            update_fields=["deleted_at"]
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Message.objects.filter(
                id=message.id
            ).exists()
        )

    def test_cannot_access_other_users_conversation(self):
        response = self.client.get(
            f"/api/conversations/{self.other_conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_create_message_in_other_users_conversation(self):
        data = {
            "sender_type": Message.SENDER_USER,
            "content": "This should not be allowed.",
        }

        response = self.client.post(
            f"/api/conversations/{self.other_conversation.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            Message.objects.filter(
                conversation=self.other_conversation,
                content="This should not be allowed.",
            ).exists()
        )

    def test_create_message_rejects_empty_content(self):
        data = {
            "sender_type": Message.SENDER_USER,
            "content": "",
        }

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_message_rejects_whitespace_content(self):
        data = {
            "sender_type": Message.SENDER_USER,
            "content": " ",
        }

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_strips_content_whitespace(self):
        data = {
            "sender_type": Message.SENDER_USER,
            "content": " Hello there ",
        }
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            data,
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["content"],
            "Hello there",
        )

    def test_message_list_defaults_to_oldest_first(self):
        first = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="First Message",
        )

        second = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Second Message",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            first.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            second.id,
        )

    def test_message_list_can_order_newest_first(self):
        first = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="First Message",
        )

        second = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Second Message",
        )

        first.created_at = timezone.now() - timezone.timedelta(minutes=1)
        first.save(update_fields=["created_at"])

        second.created_at = timezone.now()
        second.save(update_fields=["created_at"])

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?ordering=-created_at"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            second.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            first.id,
        )

    def test_message_list_can_order_oldest_first(self):
        first = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="First Message",
        )

        second = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Second Message",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?ordering=created_at"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            first.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            second.id,
        )

    def test_invalid_message_ordering_defaults_to_oldest(self):
        first = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Second Message",
        )

        second = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Second Message",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?ordering=invalid"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            first.id,
        )

        self.assertEqual(
            response.data["results"][1]["id"],
            second.id,
        )

    def test_new_message_is_unread_by_default(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Unread message",
        )

        self.assertFalse(
            message.is_read
        )

    def test_message_response_includes_read_status(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Read status test",
        )

        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            response.data["results"][0]["is_read"]
        )

    def test_message_update_cannot_change_read_status(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Original message",
        )

        response = self.client.patch(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/",
            {
                "is_read": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        message.refresh_from_db()

        self.assertFalse(
            message.is_read
        )

    def test_mark_message_as_read(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Mark me as read",
        )

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        message.refresh_from_db()

        self.assertTrue(
            message.is_read
        )

        self.assertTrue(
            response.data["is_read"]
        )

    def test_mark_already_read_message_as_read_is_safe(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Already read",
            is_read=True,
        )

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/{message.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        message.refresh_from_db()

        self.assertTrue(
            message.is_read
        )

    def test_cannot_mark_other_users_message_as_read(self):
        other_conversation = Conversation.objects.create(
            user=self.other_user,
            title="Other User Conversation",
        )

        message = Message.objects.create(
            conversation=other_conversation,
            sender_type=Message.SENDER_USER,
            content="Private message",
        )

        response = self.client.post(
            f"/api/conversations/{other_conversation.id}/messages/{message.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        message.refresh_from_db()

        self.assertFalse(
            message.is_read
        )

    def test_cannot_mark_deleted_conversation_message_as_read(self):
        conversation = self.conversation

        conversation.deleted_at = timezone.now()
        conversation.save(
            update_fields=["deleted_at"]
        )

        message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content="Deleted conversation message",
        )

        response = self.client.post(
            f"/api/conversations/{conversation.id}/messages/{message.id}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        message.refresh_from_db()

        self.assertFalse(
            message.is_read
        )

    def test_create_message_rejects_invalid_sender_type(self):
        data = {
            "sender_type": "invalid",
            "content": "This should be rejected.",
        }

        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/messages/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            Message.objects.filter(
                conversation=self.conversation,
                content="This should be rejected.",
            ).exists()
        )

class MessageDetailAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="detailuser",
            email="detailuser@example.com",
            password="StrongPass123",
        )

        self.other_user = User.objects.create_user(
            username="otherdetailuser",
            email="otherdetailuser@example.com",
            password="StrongPass123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Detail Test Conversation",
        )

        self.other_conversation = Conversation.objects.create(
            user=self.other_user,
            title="Other User Conversation",
        )

        self.message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Original message",
        )

        self.other_message = Message.objects.create(
            conversation=self.other_conversation,
            sender_type=Message.SENDER_USER,
            content="Other user's message",
        )
        self.client.force_authenticate(
            user=self.user,
        )

    def test_retrieve_message(self):
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/{self.message.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.message.id,
        )

        self.assertEqual(
            response.data["content"],
            "Original message",
        )

    def test_update_message(self):
        data = {
            "content": "Updated message",
        }
        response = self.client.patch(
            f"/api/conversations/{self.conversation.id}/messages/{self.message.id}/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["content"],
            "Updated message",
        )

        self.message.refresh_from_db()

        self.assertEqual(
            self.message.content,
            "Updated message",
        )

    def test_delete_message(self):
        response = self.client.delete(
            f"/api/conversations/{self.conversation.id}/messages/{self.message.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Message.objects.filter(
                id=self.message.id
            ).exists()
        )

    def test_cannot_retrieve_other_users_message(self):
        response = self.client.get(
            f"/api/conversations/{self.other_conversation.id}/messages/{self.other_message.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cannot_update_other_users_message(self):
        data = {
            "content": "Unauthorized update",
        }

        response = self.client.patch(
            f"/api/conversations/{self.other_conversation.id}/messages/{self.other_message.id}/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.other_message.refresh_from_db()

        self.assertEqual(
            self.other_message.content,
            "Other user's message",
        )

    def test_cannot_delete_other_users_message(self):
        response = self.client.delete(
            f"/api/conversations/{self.other_conversation.id}/messages/{self.other_message.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Message.objects.filter(
                id=self.other_message.id
            ).exists()
        )

class AIConversationServiceTestCase(TestCase):
    def setUp(self):
        from users.models import User, NIRAPersonalProfile
        from conversations.models import Conversation, Message

        self.user = User.objects.create_user(
            username="ai_profile_context_test_user",
            email="ai_profile_context_test@example.com",
            password="StrongPass123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Profile Context Test",
        )

        self.user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="What should I know about Python?",
        )

        self.profile = NIRAPersonalProfile.objects.create(
            user=self.user,
            languages=["English"],
            communication_style={
                "tone": "professional",
            },
            interests=["AI", "Python"],
        )

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_personal_profile_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        mock_generate_response.return_value = (
            "Python is a programming language."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Personal profile context:",
            prompt,
        )
        self.assertIn(
            "Languages:",
            prompt,
        )
        self.assertIn(
            "English",
            prompt,
        )
        self.assertIn(
            "Communication Style:",
            prompt,
        )
        self.assertIn(
            "professional",
            prompt,
        )
        self.assertIn(
            "Interests:",
            prompt,
        )
        self.assertIn(
            "AI",
            prompt,
        )

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_combines_profile_and_knowledge_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        mock_generate_response.return_value = (
            "Python is a programming language."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            rag_context="Python backend knowledge",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Personal profile context:",
            prompt,
        )

        self.assertIn(
            "Languages:",
            prompt,
        )

        self.assertIn(
            "English",
            prompt,
        )

        self.assertIn(
            "Knowledge context:",
            prompt,
        )

        self.assertIn(
            "Python backend knowledge",
            prompt,
        )

        self.assertIn(
            "User question:",
            prompt,
        )

        self.assertIn(
            self.user_message.content,
            prompt,
        )

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_combines_profile_conversation_and_knowledge_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        from conversations.models import Message

        mock_generate_response.return_value = (
            "Python is a programming language."
        )

        previous_message = Message.objects.create(
            conversation=self.conversation,
            sender_type="user",
            content="I am working on a Django backend project.",
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            rag_context="Python backend knowledge",
        )

        prompt = mock_generate_response.call_args.args[0]
        messages = mock_generate_response.call_args.kwargs["messages"]

        self.assertIn(
            "Personal profile context:",
            prompt,
        )

        self.assertIn(
            "English",
            prompt,
        )

        self.assertIn(
            "Knowledge context:",
            prompt,
        )

        self.assertIn(
            "Python backend knowledge",
            prompt,
        )

        self.assertIn(
            "User question:",
            prompt,
        )

        self.assertIn(
            self.user_message.content,
            prompt,
        )

        self.assertTrue(
            any(
                message["role"] == "user"
                and message["content"]
                == previous_message.content
                for message in messages
            )
        )       

    def test_generate_response_uses_only_conversation_user_profile(self):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        other_user = User.objects.create_user(
            username="other_profile_user",
            email="other_profile@example.com",
            password="StrongPass123",
        )

        NIRAPersonalProfile.objects.create(
            user=other_user,
            work_info={
                "role": "Other User Private Role",
            },
            skills=[
                "Private Skill",
            ],
        )

        service = AIConversationService()

        result = service._build_ai_profile_context(
            self.conversation,
            context_purpose="work",
        )

        self.assertNotIn(
            "Other User Private Role",
            result,
        )

        self.assertNotIn(
            "Private Skill",
            result,
        ) 

    def test_build_ai_profile_context_handles_missing_profile(self):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )
        from users.models import User

        self.profile.delete()

        service = AIConversationService()

        result = service._build_ai_profile_context(
            self.conversation,
            context_purpose="general",
        )

        self.assertEqual(
            result,
            "",
        )

        self.assertTrue(
            NIRAPersonalProfile.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_build_ai_profile_context_uses_filtered_profile_context(self):
         
        self.profile.work_info = {
            "role": "Python Backend Developer",
        }
        self.profile.skills = [
            "Python",
            "Django",
        ]
        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        service = AIConversationService()
    
        result = service._build_ai_profile_context(
            self.conversation,
            context_purpose="work",
        )

        self.assertIn(
            "Work Information:",
            result,
        )

        self.assertIn(
            "Python Backend Developer",
            result,
        )

        self.assertIn(
            "Skills:",
            result,
        )

        self.assertIn(
            "Python",
            result,
        )

        self.assertNotIn(
            "Privacy Settings:",
            result,
        )

        self.assertNotIn(
            "Memory Settings:",
            result,
        )    

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_does_not_expose_protected_profile_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        self.profile.privacy_settings = {
            "share_profile": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Python is a programming language."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertNotIn(
            "Privacy Settings:",
            prompt,
        )
        self.assertNotIn(
            "Memory Settings:",
            prompt,
        )

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_requested_work_profile_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        self.profile.work_info = {
            "role": "Python Backend Developer",
        }
        self.profile.skills = [
            "Python",
            "Django",
        ]
        self.profile.interests = [
            "AI",
        ]
        self.profile.save()

        mock_generate_response.return_value = (
            "Python backend development requires strong API skills."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            profile_context_purpose="work",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Work Information:",
            prompt,
        )
        self.assertIn(
            "Python Backend Developer",
            prompt,
        )
        self.assertIn(
            "Skills:",
            prompt,
        )
        self.assertIn(
            "Django",
            prompt,
        )

        self.assertNotIn(
            "Interests:",
            prompt,
        )  

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_requested_communication_profile_context(
        self,
        mock_generate_response,
    ):
        from conversations.services.ai_conversation_service import (
            AIConversationService,
        )

        self.profile.languages = [
            "English",
            "Hindi",
        ]
        self.profile.communication_style = {
            "tone": "professional",
        }
        self.profile.interests = [
            "AI",
        ]
        self.profile.important_people = [
            {"name": "Test Person"},
        ]
        self.profile.work_info = {
            "role": "Developer",
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a professional response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            profile_context_purpose="communication",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Languages:",
            prompt,
        )
        self.assertIn(
            "English",
            prompt,
        )
        self.assertIn(
            "Communication Style:",
            prompt,
        )
        self.assertIn(
            "professional",
            prompt,
        )
        self.assertIn(
            "Important People:",
            prompt,
        )
        self.assertIn(
            "Test Person",
            prompt,
        )

        self.assertNotIn(
            "Work Information:",
            prompt,
        )
        self.assertNotIn(
            "Skills:",
            prompt,
        )
        self.assertNotIn(
            "Interests:",
            prompt,
        )  

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_does_not_expose_unrelated_protected_profile_info(
        self,
        mock_generate_response,
    ):
        self.profile.languages = [
            "English",
        ]
        self.profile.communication_style = {
            "tone": "professional",
        }
        self.profile.privacy_settings = {
            "allow_cloud_ai": False,
            "sensitive_data": False,
        }
        self.profile.memory_settings = {
            "enabled": True,
            "auto_save": True,
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a professional response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            profile_context_purpose="communication",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Languages:",
            prompt,
        )

        self.assertIn(
            "Communication Style:",
            prompt,
        )

        self.assertNotIn(
            "Privacy Settings:",
            prompt,
        )

        self.assertNotIn(
            "Memory Settings:",
            prompt,
        )

        self.assertNotIn(
            "allow_cloud_ai",
            prompt,
        )

        self.assertNotIn(
            "auto_save",
            prompt,
        )    

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_combines_profile_response_preferences(
        self,
        mock_generate_response,
    ):
        from users.models import Language

        preferred_language = Language.objects.get(
            name="Hindi",
        )

        self.user.preferred_language_ref = preferred_language
        self.user.save()

        self.profile.communication_style = {
            "response_style": "concise",
            "formality": "formal",
            "response_length": "short",
            "channels": {
                "whatsapp": {
                    "response_length": "very_short",
                },
            },
        }
        self.profile.custom_instructions = (
            "Always explain technical topics with a simple example."
        )
        self.profile.save()

        mock_generate_response.return_value = (
            "यह एक संक्षिप्त और स्पष्ट उत्तर है।"
        )

        service = AIConversationService()

        response = service.generate_response(
            self.conversation,
            self.user_message,
            channel="whatsapp",
            profile_context_purpose="instructions",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "preferred language",
            prompt.lower(),
        )

        self.assertIn(
            "Hindi",
            prompt,
        )

        self.assertIn(
            "response_style",
            prompt,
        )

        self.assertIn(
            "concise",
            prompt,
        )

        self.assertIn(
            "response_length",
            prompt,
        )

        self.assertIn(
            "very_short",
            prompt,
        )

        self.assertIn(
            "Custom Instructions:",
            prompt,
        )

        self.assertIn(
            "Always explain technical topics with a simple example.",
            prompt,
        )

        self.assertEqual(
            response.content,
            "यह एक संक्षिप्त और स्पष्ट उत्तर है।",
        )    

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_custom_nira_instructions(
        self,
        mock_generate_response,
    ):
        self.profile.custom_instructions = (
            "Always explain technical topics with a simple example."
        )
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a simple example."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            profile_context_purpose="instructions",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Custom Instructions:",
            prompt,
        )

        self.assertIn(
            "Always explain technical topics with a simple example.",
            prompt,
        )    

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_applies_communication_preferences(
        self,
        mock_generate_response,
    ):
        self.profile.communication_style = {
            "tone": "professional",
            "formality": "formal",
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a professional response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Apply the user's communication preferences",
            prompt,
        )

        self.assertIn(
            "Communication preferences:",
            prompt,
        )

        self.assertIn(
            "professional",
            prompt,
        )

        self.assertIn(
            "formal",
            prompt,
        )     

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_profile_aware_response_remains_natural(
        self,
        mock_generate_response,
    ):
        self.profile.communication_style = {
            "tone": "professional",
            "formality": "formal",
            "response_length": "short",
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a concise professional response "
            "that directly addresses your question."
        )

        service = AIConversationService()

        response = service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            response.content,
            "Here is a concise professional response "
            "that directly addresses your question.",
        )

        self.assertNotEqual(
            response.content.strip(),
            "",
        )

        self.assertNotIn(
            "Communication preferences:",
            response.content,
        )

        self.assertNotIn(
            "Personal profile context:",
            response.content,
        )

        self.assertNotIn(
            "Knowledge context:",
            response.content,
        )     

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_response_style(
        self,
        mock_generate_response,
    ):
        self.profile.communication_style = {
            "response_style": "concise",
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a concise response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Communication preferences:",
            prompt,
        )

        self.assertIn(
            "response_style",
            prompt,
        )

        self.assertIn(
            "concise",
            prompt,
        )   

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_response_length(
        self,
        mock_generate_response,
    ):
        self.profile.communication_style = {
            "response_length": "short",
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a short response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Communication preferences:",
            prompt,
        )

        self.assertIn(
            "response_length",
            prompt,
        )

        self.assertIn(
            "short",
            prompt,
        )  

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_channel_specific_preferences(
        self,
        mock_generate_response,
    ):
        self.profile.communication_style = {
            "response_style": "concise",
            "response_length": "short",
            "channels": {
                "whatsapp": {
                    "response_length": "very_short",
                },
            },
        }
        self.profile.save()

        mock_generate_response.return_value = (
            "Here is a very short WhatsApp response."
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
            channel="whatsapp",
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Apply the user's whatsapp communication preferences",
            prompt,
        )

        self.assertIn(
            "Whatsapp preferences:",
            prompt,
        )

        self.assertIn(
            "response_length",
            prompt,
        )

        self.assertIn(
            "very_short",
            prompt,
        )         

    @patch(
    "conversations.services.ai_conversation_service.AIService.generate_response"
    )
    def test_generate_response_uses_preferred_language(
        self,
        mock_generate_response,
    ):
        from users.models import Language

        preferred_language = Language.objects.get(
            name="Hindi",
        )

        self.user.preferred_language_ref = preferred_language
        self.user.save()

        mock_generate_response.return_value = (
            "यह हिंदी में उत्तर है।"
        )

        service = AIConversationService()

        service.generate_response(
            self.conversation,
            self.user_message,
        )

        prompt = mock_generate_response.call_args.args[0]

        self.assertIn(
            "Respond in the user's preferred language.",
            prompt,
        )

        self.assertIn(
            "The preferred language is: Hindi.",
            prompt,
        )   

class TextToSpeechAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ttstestuser",
            email="ttstest@example.com",
            password="StrongPass123",
        )

        self.client.force_authenticate(
            user=self.user,
        )
    @patch(
        "conversations.views.AIConversationService.__init__",
        return_value=None,
    )
    @patch(
        "conversations.views.AIConversationService.synthesize_speech"
    )
    def test_text_to_speech_returns_wav_audio(
        self,
        mock_synthesize_speech,
        mock_service_init,
    ):
        mock_synthesize_speech.return_value = (
            b"RIFFmockwavdata"
        )

        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "language": "en",
                "voice": "Kore",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response["Content-Type"],
            "audio/wav",
        )

        self.assertEqual(
            response.content,
            b"RIFFmockwavdata",
        )

        mock_synthesize_speech.assert_called_once_with(
            "Hello world",
            language="en",
            voice="Kore",
        )

    @patch(
        "conversations.views.AIConversationService.__init__",
        return_value=None,
    )
    @patch(
        "conversations.views.AIConversationService.synthesize_speech"
    )
    def test_text_to_speech_strips_text_language_and_voice(
        self,
        mock_synthesize_speech,
        mock_service_init,
    ):
        mock_synthesize_speech.return_value = (
            b"RIFFmockwavdata"
        )

        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "  Hello world  ",
                "language": " en ",
                "voice": " Kore ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_synthesize_speech.assert_called_once_with(
            "Hello world",
            language="en",
            voice="Kore",
        )

    @patch(
        "conversations.views.AIConversationService.__init__",
        return_value=None,
    )
    @patch(
        "conversations.views.AIConversationService.synthesize_speech"
    )
    def test_text_to_speech_allows_optional_language_and_voice(
        self,
        mock_synthesize_speech,
        mock_service_init,
    ):
        mock_synthesize_speech.return_value = (
            b"RIFFmockwavdata"
        )

        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_synthesize_speech.assert_called_once_with(
            "Hello world",
            language=None,
            voice=None,
        )

    def test_text_to_speech_rejects_empty_text(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "text",
            response.data,
        )

    def test_text_to_speech_rejects_whitespace_text(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "text",
            response.data,
        )

    def test_text_to_speech_rejects_empty_language(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "language": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["language"][0],
            "Language cannot be empty.",
        )

    def test_text_to_speech_rejects_whitespace_language(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "language": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["language"][0],
            "Language cannot be empty.",
        )

    def test_text_to_speech_rejects_empty_voice(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "voice": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["voice"][0],
            "Voice cannot be empty.",
        )

    def test_text_to_speech_rejects_whitespace_voice(self):
        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "voice": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["voice"][0],
            "Voice cannot be empty.",
        )

    @patch(
        "conversations.views.AIConversationService.__init__",
        return_value=None,
    )
    @patch(
        "conversations.views.AIConversationService.synthesize_speech"
    )
    def test_text_to_speech_returns_provider_error(
        self,
        mock_synthesize_speech,
        mock_service_init,
    ):
        mock_synthesize_speech.side_effect = (
            TextToSpeechProviderError(
                "TTS provider failed"
            )
        )

        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
                "language": "en",
                "voice": "Kore",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        self.assertEqual(
            response.data,
            {
                "error": {
                    "code": "text_to_speech_provider_error",
                    "message": (
                        "Text-to-speech service is currently unavailable."
                    ),
                }
            },
        )

    def test_text_to_speech_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            "/api/conversations/text-to-speech/",
            {
                "text": "Hello world",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

