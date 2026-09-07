from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from ai.providers.exceptions import AIProviderError

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

        call_kwargs = (
            mock_client.chat.completions.create.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["model"],
            "gpt-4o-mini",
        )

        self.assertEqual(
            call_kwargs["messages"],
            [
                {
                    "role": "user",
                    "content": "Hello AI",
                },
            ],
        )

        self.assertEqual(
            call_kwargs["temperature"],
            0.7,
        )

        self.assertEqual(
            call_kwargs["max_tokens"],
            1000,
        )

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

    @patch("ai.providers.openai.OpenAI")
    def test_generate_with_messages(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Context-aware response"
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

        self.assertEqual(
            response,
            "Context-aware response",
        )

        call_kwargs = (
            mock_client.chat.completions.create.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["messages"],
            [
                {
                    "role": "user",
                    "content": "Hello AI",
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I help?",
                },
                {
                    "role": "user",
                    "content": "What can you do?",
                },
            ],
        )

    def test_missing_api_key_raises_error(self):
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": ""},
            clear=False,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "OPENAI_API_KEY is not configured.",
            ):
                OpenAIProvider()

    @patch("ai.providers.openai.OpenAI")
    def test_generate_raises_provider_error_on_openai_failure(self, mock_openai):
        mock_client = Mock()

        mock_client.chat.completions.create.side_effect = (
            RuntimeError("OpenAI API failed")
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

        with self.assertRaisesRegex(
            AIProviderError,
            "Failed to generate response from OpenAI.",
        ):
            provider.generate("Hello AI") 

    @patch("ai.providers.openai.OpenAI")
    def test_generate_with_system_prompt_and_messages(self, mock_openai):
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content="Context-aware response"
                )
            )
        ]    

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = (mock_response)
        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "OPEANAI_MODEL": "gpt-4o-mini",
            },
        ):
            provider = OpenAIProvider()

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
            "What can you help me with?",
            system_prompt="You are a helpful assistant.",
            messages=messages,
        )                     

        self.assertEqual(
            response,
            "Context-aware response",
        )  

        call_kwargs = (
            mock_client.chat.completions.create.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["messages"],
            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": "Hello AI",
                },
                {
                    "role": "assistant",
                    "content": "Hello! How can I help?",
                },
                {
                    "role": "user",
                    "content": "What can you help me with?",
                },
            ],
        )

    @patch("ai.providers.openai.OpenAI")
    def test_generate_stream_response(self, mock_openai):
        chunks = [
            Mock(
                choices=[
                    Mock(
                        delta=Mock(content="Hello")
                    )
                ]
            ),
            Mock(
                choices=[
                    Mock(
                        delta=Mock(content="from OpenAI")
                    )
                ]
            ),
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = chunks

        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "OPENAI_MODEL": "gpt-4o-mini",
            },
        ):
            provider = OpenAIProvider()

        result = list(
            provider.generate_stream("Hello AI")
        )

        self.assertEqual(
            result,
            ["Hello", "from OpenAI"],
        )       

        call_kwargs = (
            mock_client.chat.completions.create.call_args.kwargs
        )

        self.assertTrue(
            call_kwargs["stream"]
        )

    @patch("ai.providers.openai.OpenAI")
    def test_generate_stream_with_system_prompt(self, mock_openai):
        chunks = [
            Mock(
                choices=[
                    Mock(
                        delta=Mock(content="Hello")
                    )
                ]
            )
        ] 

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = chunks

        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-api-key",
                "OPENAI_MODEL": "gpt-4o-mini",
            },
        ):
            provider = OpenAIProvider()

        result = list(
            provider.generate_stream(
                "Hello AI",
                system_prompt="You are helpful.",
            )
        )       

        self.assertEqual(
            result,
            ["Hello"],
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

        self.assertTrue(
            call_kwargs["stream"]
        )

    @patch("ai.providers.openai.OpenAI")
    def test_generate_stream_raise_provider_error(
        self,
        mock_openai,
    ):
        mock_client = Mock()

        mock_client.chat.completions.create.side_effect = (
            RuntimeError("OpenAI streaming failed")
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

        with self.assertRaisesRegex(
            AIProviderError,
            "Failed to generate streaming response from OpenAI.",
        ):
            list(
                provider.generate_stream("Hello AI")
            )   