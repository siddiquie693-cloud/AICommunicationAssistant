from unittest.mock import patch
from django.test import TestCase

from conversations.models import Conversation, Message
from conversations.services.ai_conversation_service import (
    AIConversationService,
)
from users.models import User


class AIConversationServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Test Conversation",
        )

        self.user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="Hello AI",
        )

        self.service = AIConversationService(
            provider_name="mock",
        )

    def test_generate_response_creates_assistant_message(self):
        assistant_message = self.service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertIsInstance(
            assistant_message,
            Message,
        )

        self.assertEqual(
            assistant_message.conversation,
            self.conversation,
        )

        self.assertEqual(
            assistant_message.sender_type,
            Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            assistant_message.content,
            "Mock AI response: Hello AI",
        )

    def test_generate_response_saves_message(self):
        self.service.generate_response(
            self.conversation,
            self.user_message,
        )

        self.assertEqual(
            self.conversation.messages.count(),
            2,
        )

    @patch(
        "conversations.services.ai_conversation_service.get_ai_provider"
    )
    @patch(
        "conversations.services.ai_conversation_service.config"
    )    
    def test_provider_is_loaded_from_environment(
        self,
        mock_config,
        mock_get_ai_provider,
    ):
        mock_config.return_value = "mock"

        service = AIConversationService()

        mock_config.assert_called_once_with(
            "AI_PROVIDER",
            default="mock",
        )

        mock_get_ai_provider.assert_called_once_with(
            "mock",
        )

        self.assertIsNotNone(
            service.ai_service,
        )