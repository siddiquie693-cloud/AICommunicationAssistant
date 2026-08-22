from django.test import SimpleTestCase

from ai.providers.factory import get_ai_provider
from ai.providers.mock import MockAIProvider


class AIProviderFactoryTests(SimpleTestCase):

    def test_get_mock_provider(self):
        provider = get_ai_provider("mock")

        self.assertIsInstance(
            provider,
            MockAIProvider,
        )

    def test_mock_provider_generates_response(self):
        provider = get_ai_provider("mock")

        response = provider.generate(
            "Hello AI"
        )

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_invalid_provider_raises_error(self):
        with self.assertRaises(ValueError) as context:
            get_ai_provider("invalid")

        self.assertEqual(
            str(context.exception),
            "Unsupported AI provider: invalid",
        )