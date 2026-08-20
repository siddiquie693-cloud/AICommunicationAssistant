from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

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
