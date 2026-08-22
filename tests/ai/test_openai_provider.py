from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from ai.providers.openai import OpenAIProvider

class OpenAIProviderTests(SimpleTestCase):

    @patch("ai.providers.openai.OpenAI")
    def test_generate_response(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Hello from OpenAI"
                )
            )
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = (
            mock_response
        )

        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "OPENAI_MODEL": "gpt-4o-mini",
            },
        ):
            provider = OpenAIProvider()

        response = provider.generate("Hello AI")

        self.assertEqual(
            response,
            "Hello from OpenAI",
        )    

        mock_client.chat.completions.create.assert_called_once()

    @patch("ai.providers.openai.OpenAI")
    def test_generate_with_system_prompt(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="System-aware response"
                )
            )
        ] 

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = (
            mock_response
        )   

        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "OPENAI_MODEL": "gpt-4o-mini",
            },
        ):
            provider = OpenAIProvider()

        response = provider.generate(
            "Hello AI",
            system_prompt="You are helpful.",
        )    

        self.assertEqual(
            response,
            "System-aware response",
        )

        call_kwargs = (
            mock_client.chat.completions.create.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["messages"],
            [
                {
                    "role": "system",
                    "content": "You are helpful.",
                },
                {
                    "role": "user",
                    "content": "Hello AI",
                },
            ],
        )

    def test_missing_api_key_raises_error(self):
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                OpenAIProvider()    