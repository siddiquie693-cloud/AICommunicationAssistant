
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.utils import timezone
from ai.providers.exceptions import AIProviderError

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

    def test_create_message_uses_conversation_history(self):
        first_response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "Hello AI",
            },
            format="json",
        )    

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            self.url,
            {
                "sender_type": "user",
                "content": "What can you help me with?",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        assistant_messages = Message.objects.filter(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
        ).order_by("created_at", "id")

        self.assertEqual(
            assistant_messages.count(),
            2,
        )

        second_assistant_message = assistant_messages[1]

        self.assertEqual(
            second_assistant_message.content,
            (
                "Mock AI response: "
                "User: Hello AI\n"
                "Assistant: Mock AI response: Hello AI"
            ),
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_response")
    def test_ai_provider_failure_returns_service_unavailable(self, mock_generate_response):
        mock_generate_response.side_effect = AIProviderError(
            "AI provider failed."
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
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertEqual(
            response.data["detail"],
            "AI service is temporarily unavailable.",
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_response")
    def test_ai_provider_failure_does_not_create_assistant_message(self, mock_generate_response):
        mock_generate_response.side_effect = AIProviderError("AI provider failed.")

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
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
            ).count(),
            1,
        )

        self.assertEqual(
            Message.objects.filter(
                conversation=self.conversation,
                sender_type=Message.SENDER_ASSISTANT,
            ).count(),
            0,
        )

    @patch("conversations.views.AIConversationService.generate_stream")
    def test_stream_message_returns_streaming_response(
        self,
        mock_generate_stream,
    ):
        mock_generate_stream.return_value = iter(
            ["Hello ", "from ", "AI"]
        )    

        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.get("Content-Type"),
            "text/plain",
        )

        self.assertEqual(
            b"".join(response.streaming_content),
            b"Hello from AI",
        )

    def test_stream_message_requires_authentication(self):
        self.client.force_authenticate(user=None)

        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )    

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_stream_message_rejects_empty_content(self):
        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )    

        response = self.client.post(
            url,
            {
                "content": "  ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_stream_message_creates_user_message(self):
        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )    

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            Message.objects.filter(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
                content="Hello AI",
            ).exists()
        )

    def test_stream_message_rejects_deleted_conversation(self):
        self.conversation.deleted_at = timezone.now() 
        self.conversation.save(update_fields=["deleted_at"])

        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )   

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_stream_message_saves_assistant_message(self):
        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )    

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        streamed_content = b"".join(
            response.streaming_content
        )

        self.assertEqual(
            streamed_content,
            b"Mock AI response: Hello AI",
        )

        self.assertTrue(
            Message.objects.filter(
                conversation=self.conversation,
                sender_type=Message.SENDER_ASSISTANT,
                content="Mock AI response: Hello AI",
            ).exists()
        )

    @patch("conversations.views.AIConversationService.generate_stream")
    def test_stream_message_handles_ai_provider_failure(
        self,
        mock_generate_stream,
    ):
        def failing_stream(*args, **kwargs):
            raise AIProviderError(
                "Provider unavailable"
            )
            yield
        mock_generate_stream.side_effect = failing_stream

        url = reverse(
            "message-stream",
            kwargs={
                "conversation_id": self.conversation.id,
            },
        )    

        response = self.client.post(
            url,
            {
                "content": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        streamed_content = b"".join(
            response.streaming_content
        )

        self.assertEqual(
            streamed_content,
            b"",
        )
        
