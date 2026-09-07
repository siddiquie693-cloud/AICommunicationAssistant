from unittest.mock import patch

from django.test import TestCase
from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
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
    def test_provider_is_loaded_from_factory(
        self,
        mock_get_ai_provider,
    ):
        mock_provider = object()
        mock_get_ai_provider.return_value = mock_provider

        service = AIConversationService()

        mock_get_ai_provider.assert_called_once_with(None)

        self.assertIsNotNone(
            service.ai_service,
        )

    def test_generate_response_includes_conversation_history(self):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Hello! How can I help?",
        )

        second_user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="What can you help me with?",
        )

        assistant_message = self.service.generate_response(
            self.conversation,
            second_user_message,
        )
        self.assertEqual(
            assistant_message.content,
            (
                "Mock AI response: "
                "User: Hello AI\n"
                "Assistant: Hello! How can I help?"
            ),
        )

    @patch("conversations.services.ai_conversation_service.config")
    def test_memory_message_limit(
        self,
        mock_config,
    ):
        mock_config.side_effect = (
            lambda key, default=None, cast=None: (
                3
                if key == "AI_MEMORY_MESSAGE_LIMIT"
                else default
            )
        )

        service = AIConversationService(
            provider_name="mock",
        )

        for index in range(5):
            Message.objects.create(
                conversation=self.conversation,
                sender_type=Message.SENDER_USER,
                content=f"Message {index}",
            )

        messages = service._build_messages(
            self.conversation,
            exclude_message_id=self.user_message.id,
        )    

        self.assertEqual(
            len(messages),
            3,
        )

        self.assertEqual(
            messages[0]["content"],
            "Message 2",
        )

        self.assertEqual(
            messages[1]["content"],
            "Message 3",
        )

        self.assertEqual(
            messages[2]["content"],
            "Message 4",
        )

    @patch("conversations.services.ai_conversation_service.config")
    def test_memory_message_limit_default_to_20(self, mock_config):
        mock_config.side_effect = (
            lambda key, default=None, cast=None: default
        )

        service = AIConversationService(
            provider_name="mock",
        )

        self.assertEqual(
            service.memory_message_limit,
            20,
        )

        mock_config.assert_called_once_with(
            "AI_MEMORY_MESSAGE_LIMIT",
            default=20,
            cast=int,
        )

    @patch("conversations.services.ai_conversation_service.config")
    def test_memory_message_limit_zero(self, mock_config):
        mock_config.side_effect = (
            lambda key, default=None, cast=None: (
                0
                if key == "AI_MEMORY_MESSAGE_LIMIT"
                else default
            )
        )    

        service = AIConversationService(
            provider_name="mock"
        )

        messages = service._build_messages(
            self.conversation,
            exclude_message_id=self.user_message.id,
        )

        self.assertEqual(
            messages,
            [],
        )

    @patch("conversations.services.ai_conversation_service.config")
    def test_negative_memory_message_limit_raises_error(self, mock_config):
        mock_config.side_effect = (
            lambda key, default=None, cast=None: (
                -1
                if key == "AI_MEMORY_MESSAGE_LIMIT"
                else default
            )
        )    

        with self.assertRaisesRegex(
            ValueError,
            "AI_MEMORY_MESSAGE_LIMIT cannot be negative.",
        ):
            AIConversationService(
                provider_name="mock",
            )

    def test_current_user_message_is_excluded_from_memory(self):
        messages = self.service._build_messages(
            self.conversation,
            exclude_message_id=self.user_message.id,
        )        

        self.assertEqual(
            messages,
            [],
        )

    @patch(
        "conversations.services.ai_conversation_service.CONVERSATION_SYSTEM_PROMPT",
        "Test system prompt",
    )    
    @patch("conversations.services.ai_conversation_service.AIService.generate_response")
    def test_generate_response_uses_conversation_system_prompt(self, mock_generate_response):
        mock_generate_response.return_value = "AI response"

        assistant_message = self.service.generate_response(
            self.conversation,
            self.user_message,
        )

        mock_generate_response.assert_called_once_with(
            "Hello AI",
            system_prompt="Test system prompt",
            messages=[],
        )

        self.assertEqual(
            assistant_message.content,
            "AI response",
        )

    @patch(
        "conversations.services.ai_conversation_service.AIService.generate_response"
    )    
    def test_generate_response_passes_system_prompt_and_history(
        self,
        mock_generate_response,
    ):
        mock_generate_response.return_value = "AI response"

        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Hello! How can I help?",
        )

        second_user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="What can you do?",
        )

        assistant_message = self.service.generate_response(
            self.conversation,
            second_user_message,
        )

        mock_generate_response.assert_called_once_with(
            "What can you do?",
            system_prompt=(
                "You are a helpful AI communication assistant. "
                "Answer clearly, accurately, and naturally. "
                "Maintain context from the conversation history."
            ),
            messages=[
                {
                    "role": "user",
                    "content": "Hello AI",
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I help?",
                },
            ],
        )

        self.assertEqual(
            assistant_message.content,
            "AI response",
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_response")
    def test_empty_ai_response_raises_error(self, mock_generate_response):
        mock_generate_response.return_value = ""

        with self.assertRaisesRegex(
            ValueError,
            "AI response cannot be empty.",
        ):
            self.service.generate_response(
                self.conversation,
                self.user_message,
            )    

        self.assertEqual(
            self.conversation.messages.count(),
            1,
        )   

    @patch("conversations.services.ai_conversation_service.AIService.generate_stream")
    def test_generate_stream(self, mock_generate_stream):
        mock_generate_stream.return_value = iter(
            ["Hello ", "from ", "AI"]
        )     

        chunks = list(
            self.service.generate_stream(
                self.conversation,
                self.user_message,
            )
        )

        self.assertEqual(
            chunks,
            ["Hello ", "from ", "AI"],
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_stream")
    def test_generate_stream_uses_conversation_history(
        self,
        mock_generate_stream,
    ):
        Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content="Hello! How can I help?",
        )    

        second_user_message = Message.objects.create(
            conversation=self.conversation,
            sender_type=Message.SENDER_USER,
            content="What can you do?",
        )

        mock_generate_stream.return_value = iter(
            ["AI ", "response"]
        )

        chunks = list(
            self.service.generate_stream(
                self.conversation,
                second_user_message,
            )
        )

        self.assertEqual(
            chunks,
            ["AI ", "response"],
        )

        mock_generate_stream.assert_called_once_with(
            "What can you do?",
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": "Hello AI",
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I help?",
                },
            ],
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_stream")
    def test_generate_stream_saves_assistant_message(
        self,
        mock_generate_stream,
    ):
        mock_generate_stream.return_value = iter(
            ["Hello ", "from ", "AI"]
        )    

        chunks = list(
            self.service.generate_stream(
                self.conversation,
                self.user_message,
            )
        )

        self.assertEqual(
            chunks,
            ["Hello ", "from ", "AI"],
        )

        assistant_message = Message.objects.get(
            conversation=self.conversation,
            sender_type=Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            assistant_message.content,
            "Hello from AI",
        )

    @patch("conversations.services.ai_conversation_service.AIService.generate_stream")
    def test_generate_stream_empty_response_does_not_save_message(
        self,
        mock_generate_stream,
    ):
        mock_generate_stream.return_value = iter([])

        chunks = list(
            self.service.generate_stream(
                self.conversation,
                self.user_message,
            )
        )

        self.assertEqual(chunks, [])

        self.assertFalse(
            Message.objects.filter(
                conversation=self.conversation,
                sender_type=Message.SENDER_ASSISTANT,
            ).exists()
        )



