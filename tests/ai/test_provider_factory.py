from unittest.mock import patch
from django.test import SimpleTestCase

from ai.providers.factory import get_ai_provider
from ai.providers.mock import MockAIProvider
from ai.providers.openai import OpenAIProvider


class ProviderFactoryTests(SimpleTestCase):

    def test_get_mock_provider(self):
        provider = get_ai_provider("mock")

        self.assertIsInstance(
            provider,
            MockAIProvider,
        )
    @patch("ai.providers.factory.OpenAIProvider")
    def test_openai_provider(self, mock_provider):
        provider = get_ai_provider("openai")

        mock_provider.assert_called_once()
        self.assertIs(
            provider,
            mock_provider.return_value,
        )

    def test_provider_name_is_case_insenstive(self):
        provider = get_ai_provider("MoCk")

        self.assertIsInstance(
            provider,
            MockAIProvider,
        )    

    def test_provider_name_is_trimmed(self):
        provider = get_ai_provider(" mock ")

        self.assertIsInstance(
            provider,
            MockAIProvider,
        )    

    def test_unsupported_provider_raises_error(self):
        with self.assertRaises(ValueError) as context:
            get_ai_provider("invalid")

        self.assertEqual(
            str(context.exception),
            "Unsupported AI provider: invalid",
        )        