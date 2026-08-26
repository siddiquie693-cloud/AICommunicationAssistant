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

    def test_generate_response_forwards_system_prompt_and_messages(self):
        provider = Mock()
        provider.generate.return_value = "AI response"

        service = AIService(provider)

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

        response = service.generate_response(
            "What can you do?",
            system_prompt="You are a helpful assistant.",
            messages=messages,
        )   

        self.assertEqual(
            response,
            "AI response",
        )

        provider.generate.assert_called_once_with(
            "What can you do?",
            system_prompt="You are a helpful assistant.",
            messages=messages,
        )