
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from ai.providers.exceptions import AIProviderError
from ai.providers.gemini import GeminiProvider


class GeminiProviderTests(SimpleTestCase):

    def create_provider(self, mock_client):
        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "test-api-key",
                "GEMINI_MODEL": "gemini-3.6-flash",
                "GEMINI_TEMPERATURE": "0.7",
                "GEMINI_MAX_TOKENS": "1000",
                "GEMINI_THINKING_BUDGET": "0",
            },
        ):
            with patch(
                "ai.providers.gemini.genai.Client",
                return_value=mock_client,
            ):
                return GeminiProvider()

    def test_generate_response(self):
        mock_client = Mock()
        mock_client.models.generate_content.return_value = Mock(
            text="Hello from Gemini"
        )

        provider = self.create_provider(mock_client)

        response = provider.generate("Hello AI")

        self.assertEqual(response, "Hello from Gemini")
        mock_client.models.generate_content.assert_called_once()

        call_kwargs = (
            mock_client.models.generate_content.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["model"],
            "gemini-3.6-flash",
        )

        self.assertEqual(
            call_kwargs["contents"][-1].parts[0].text,
            "Hello AI",
        )

    def test_generate_with_system_prompt(self):
        mock_client = Mock()
        mock_client.models.generate_content.return_value = Mock(
            text="System-aware response"
        )

        provider = self.create_provider(mock_client)

        response = provider.generate(
            "Hello AI",
            system_prompt="You are helpful.",
        )

        self.assertEqual(response, "System-aware response")

        call_kwargs = (
            mock_client.models.generate_content.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["config"].system_instruction,
            "You are helpful.",
        )

    def test_generate_with_messages(self):
        mock_client = Mock()
        mock_client.models.generate_content.return_value = Mock(
            text="Context-aware response"
        )

        provider = self.create_provider(mock_client)

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

        response = provider.generate(
            "What can you do?",
            messages=messages,
        )

        self.assertEqual(response, "Context-aware response")

        call_kwargs = (
            mock_client.models.generate_content.call_args.kwargs
        )

        contents = call_kwargs["contents"]

        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0].role, "user")
        self.assertEqual(contents[1].role, "model")
        self.assertEqual(contents[2].role, "user")

    def test_generate_returns_empty_string_when_response_has_no_text(self):
        mock_client = Mock()
        mock_client.models.generate_content.return_value = Mock(
            text=None
        )

        provider = self.create_provider(mock_client)

        response = provider.generate("Hello AI")

        self.assertEqual(response, "")

    def test_generate_raises_provider_error(self):
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = (
            RuntimeError("Gemini API failed")
        )

        provider = self.create_provider(mock_client)

        with self.assertRaisesRegex(
            AIProviderError,
            "Failed to generate response from Gemini.",
        ):
            provider.generate("Hello AI")

    def test_generate_stream_response(self):
        mock_client = Mock()

        mock_client.models.generate_content_stream.return_value = [
            Mock(text="Hello"),
            Mock(text=" from Gemini"),
        ]

        provider = self.create_provider(mock_client)

        response = list(
            provider.generate_stream("Hello AI")
        )

        self.assertEqual(
            response,
            ["Hello", " from Gemini"],
        )

        mock_client.models.generate_content_stream.assert_called_once()

    def test_generate_stream_with_system_prompt(self):
        mock_client = Mock()

        mock_client.models.generate_content_stream.return_value = [
            Mock(text="Hello"),
        ]

        provider = self.create_provider(mock_client)

        response = list(
            provider.generate_stream(
                "Hello AI",
                system_prompt="You are helpful.",
            )
        )

        self.assertEqual(response, ["Hello"])

        call_kwargs = (
            mock_client.models.generate_content_stream.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["config"].system_instruction,
            "You are helpful.",
        )

    def test_generate_stream_raises_provider_error(self):
        mock_client = Mock()

        mock_client.models.generate_content_stream.side_effect = (
            RuntimeError("Gemini streaming failed")
        )

        provider = self.create_provider(mock_client)

        with self.assertRaisesRegex(
            AIProviderError,
            "Failed to generate streaming response from Gemini.",
        ):
            list(
                provider.generate_stream("Hello AI")
            )

    @patch("ai.providers.gemini.time.sleep")
    def test_generate_retries_after_503(self, mock_sleep):
        mock_client = Mock()

        mock_client.models.generate_content.side_effect = [
            RuntimeError("503 UNAVAILABLE"),
            Mock(text="Recovered response"),
        ]

        provider = self.create_provider(mock_client)

        response = provider.generate("Hello AI")

        self.assertEqual(response, "Recovered response")
        self.assertEqual(
            mock_client.models.generate_content.call_count,
            2,
        )
        mock_sleep.assert_called_once_with(1.0)

    @patch("ai.providers.gemini.time.sleep")
    def test_generate_retries_after_429(self, mock_sleep):
        mock_client = Mock()

        mock_client.models.generate_content.side_effect = [
            RuntimeError("429 RESOURCE_EXHAUSTED"),
            Mock(text="Recovered response"),
        ]

        provider = self.create_provider(mock_client)

        response = provider.generate("Hello AI")

        self.assertEqual(response, "Recovered response")
        self.assertEqual(
            mock_client.models.generate_content.call_count,
            2,
        )
        mock_sleep.assert_called_once_with(1.0)

    @patch("ai.providers.gemini.time.sleep")
    def test_generate_stops_after_maximum_retries(self, mock_sleep):
        mock_client = Mock()

        mock_client.models.generate_content.side_effect = (
            RuntimeError("503 UNAVAILABLE")
        )

        provider = self.create_provider(mock_client)

        with self.assertRaises(AIProviderError):
            provider.generate("Hello AI")

        self.assertEqual(
            mock_client.models.generate_content.call_count,
            3,
        )

        self.assertEqual(mock_sleep.call_count, 2)

    @patch("ai.providers.gemini.time.sleep")
    def test_generate_stream_retries_before_first_chunk(
        self,
        mock_sleep,
    ):
        mock_client = Mock()

        mock_client.models.generate_content_stream.side_effect = [
            RuntimeError("503 UNAVAILABLE"),
            [Mock(text="Recovered stream")],
        ]

        provider = self.create_provider(mock_client)

        response = list(
            provider.generate_stream("Hello AI")
        )

        self.assertEqual(
            response,
            ["Recovered stream"],
        )

        self.assertEqual(
            mock_client.models.generate_content_stream.call_count,
            2,
        )

        mock_sleep.assert_called_once_with(1.0)

    @patch("ai.providers.gemini.time.sleep")
    def test_generate_stream_does_not_retry_after_first_chunk(
        self,
        mock_sleep,
    ):
        mock_client = Mock()

        def failing_stream():
            yield Mock(text="Partial response")
            raise RuntimeError("503 UNAVAILABLE")

        mock_client.models.generate_content_stream.return_value = (
            failing_stream()
        )

        provider = self.create_provider(mock_client)

        with self.assertRaises(AIProviderError):
            list(
                provider.generate_stream("Hello AI")
            )

        self.assertEqual(
            mock_client.models.generate_content_stream.call_count,
            1,
        )

        mock_sleep.assert_not_called()
        