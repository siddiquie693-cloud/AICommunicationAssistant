
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from conversations.models import Conversation, Message


User = get_user_model()


class AIMessageAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="AI Test Conversation",
        )

        self.url = reverse(
            "message-list-create",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )

    def test_create_message_generates_ai_response(self):
        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
            ).count(),
            2,
        )

        user_message = Message.objects.get(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
        )

        assistant_message = Message.objects.get(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            user_message.content,
            "Hello AI",
        )

        self.assertEqual(
            assistant_message.content,
            "Mock AI response: Hello AI",
        )

    def test_ai_response_belongs_to_same_conversation(self):
        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Test conversation",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        assistant_message = Message.objects.get(
            sender_type=Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            assistant_message.conversation,
            self.conversation,
        )

    def test_ai_response_has_assistant_sender_type(self):
        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Who are you?",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        assistant_message = Message.objects.get(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            assistant_message.sender_type,
            Message.SENDER_ASSISTANT,
        )

    def test_empty_message_content_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
            ).count(),
            0,
        )

    def test_deleted_conversation_cannot_receive_message(self):
        from django.utils import timezone

        self.conversation.deleted_at = timezone.now()
        self.conversation.save(
            update_fields=["deleted_at"],
        )

        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
            ).count(),
            0,
        )

    def test_create_message_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
