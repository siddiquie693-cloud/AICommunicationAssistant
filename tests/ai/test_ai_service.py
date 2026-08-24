from django.test import SimpleTestCase

from ai.providers.mock import MockAIProvider
from ai.providers.exceptions import AIProviderError
from ai.services.ai_service import AIService
from unittest.mock import Mock

class AIServiceTests(SimpleTestCase):

    def setUp(self):
        self.provider = MockAIProvider()
        self.service = AIService(self.provider)

    def test_generate_response(self):
        response = self.service.generate_response(
            "Hello AI"
        )

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_response_strips_prompt(self):
        response = self.service.generate_response(
            "  Hello AI  "
        )

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_empty_prompt_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.generate_response("")

    def test_generate_response_with_system_prompt(self):
        response = self.service.generate_response(
            "Hello AI",
            system_prompt="You are a helful assistant.",
        )        

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_response_with_messages(self):
        messages = [
            {
                "role": "user",
                "content": "Hello AI",
            },
            {
                "role": "assistant",
                "content": "Hello! How can I help?",
            },
        ]    

        response = self.service.generate_response(
            "What can you do?",
            messages=messages,
        )

        self.assertEqual(
            response,
            "Mock AI response: "
            "User: Hello AI\n"
            "Assistant: Hello! How can I help?",
        )

    def test_provider_error_is_propagated(self):
        provider = Mock()
        provider.generate.side_effect = AIProviderError(
            "AI provider failed."
        )    

        service = AIService(provider)

        with self.assertRaisesRegex(
            AIProviderError,
            "AI provider failed.",
        ):
            service.generate_response("Hello AI")