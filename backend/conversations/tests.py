from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Conversation, Message

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

        self.assertEqual(len(response.data), 2)

        self.assertEqual(
            response.data[0]["content"],
            "Hello",
        )

        self.assertEqual(
            response.data[1]["sender_type"],
            Message.SENDER_ASSISTANT,
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
