from django.test import SimpleTestCase

from ai.providers.mock import MockAIProvider
from ai.providers.exceptions import AIProviderError
from ai.services.ai_service import AIService
from unittest.mock import Mock
from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
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

    def test_generate_response_uses_default_system_prompt(self):
        provider = Mock()
        provider.generate.return_value = "AI response"

        service = AIService(provider)

        response = service.generate_response("Hello AI")

        self.assertEqual(response, "AI response")

        provider.generate.assert_called_once_with(
            "Hello AI",
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            messages=None,
        )  

    def test_generate_stream(self):
        chunks = list(
            self.service.generate_stream("Hello AI")
        )    

        self.assertGreater(len(chunks), 1)

        response = "".join(chunks)

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_stream_strips_prompt(self):
        chunks = list(
            self.service.generate_stream(
                " Hello AI "
            )
        )    

        response = "".join(chunks)

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_stream_with_system_prompt(self):
        chunks = list(
            self.service.generate_stream(
                "Hello AI",
                system_prompt="You are helful.",
            )
        )    

        response = "".join(chunks)

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_stream_with_messages(self):
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

        chunks = list(
            self.service.generate_stream(
                "what can you do?",
                messages=messages,
            )
        )

        response = "".join(chunks)

        self.assertEqual(
            response,
            "Mock AI response: "
            "User: Hello AI\n"
            "Assistant: Hello! How can I help?",
        )

    def test_generate_stream_empty_prompt_raises_error(self):
        with self.assertRaises(ValueError):
            list(
                self.service.generate_stream("")
            )    

    def test_generate_stream_forwards_arguments(self):
        provider = Mock()

        provider.generate_stream.return_value = iter(
            ["Hello ", "AI"]
        )        

        service = AIService(provider)

        messages = [
            {
                "role": "user",
                "content": "Previous message",
            },
        ]

        chunks = list(
            service.generate_stream(
                "Current message",
                system_prompt="You are helpful.",
                messages=messages,
            )
        )

        self.assertEqual(
            chunks,
            ["Hello ", "AI"],
        )

        provider.generate_stream.assert_called_once_with(
            "Current message",
            system_prompt="You are helpful.",
            messages=messages,
        )

    def test_generate_stream_uses_default_system_prompt(self):
        provider = Mock()
        provider.generate_stream.return_value = iter(
            ["AI response"]
        )    

        service = AIService(provider)

        chunks = list(
            service.generate_stream("Hello AI")
        )

        self.assertEqual(
            chunks,
            ["AI response"],
        )

        provider.generate_stream.assert_called_once_with(
            "Hello AI",
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            messages=None,
        )