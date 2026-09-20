import io
import os
import wave
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from ai.text_to_speech.exceptions import TextToSpeechProviderError
from ai.text_to_speech.gemini import GeminiTextToSpeechProvider


class GeminiTextToSpeechProviderTests(SimpleTestCase):

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_init_uses_explicit_api_key(self, mock_client):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        mock_client.assert_called_once_with(
            api_key="test-api-key"
        )
        self.assertEqual(
            provider.model,
            "gemini-3.1-flash-tts-preview",
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_init_requires_api_key(self):
        with self.assertRaisesMessage(
            ValueError,
            "GOOGLE_API_KEY or GEMINI_API_KEY is required.",
        ):
            GeminiTextToSpeechProvider()

    @patch("ai.text_to_speech.gemini.genai.Client")
    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "google-key"},
        clear=True,
    )
    def test_init_uses_google_api_key(
        self,
        mock_client,
    ):
        GeminiTextToSpeechProvider()

        mock_client.assert_called_once_with(
            api_key="google-key"
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "gemini-key"},
        clear=True,
    )
    def test_init_uses_gemini_api_key(
        self,
        mock_client,
    ):
        GeminiTextToSpeechProvider()

        mock_client.assert_called_once_with(
            api_key="gemini-key"
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_returns_wav_audio(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        pcm_data = b"\x00\x01" * 100

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = pcm_data

        provider.client.models.generate_content.return_value = (
            response
        )

        result = provider.synthesize(
            "Hello world",
            language="en",
            voice="Kore",
        )

        self.assertTrue(
            result.startswith(b"RIFF")
        )
        self.assertIn(
            b"WAVE",
            result[:20],
        )

        with wave.open(io.BytesIO(result), "rb") as wav_file:
            self.assertEqual(
                wav_file.getnchannels(),
                1,
            )
            self.assertEqual(
                wav_file.getsampwidth(),
                2,
            )
            self.assertEqual(
                wav_file.getframerate(),
                24000,
            )
            self.assertEqual(
                wav_file.readframes(100),
                pcm_data,
            )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_strips_text(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = b"\x00\x01"

        provider.client.models.generate_content.return_value = (
            response
        )

        provider.synthesize(
            "  Hello world  ",
            language="en",
        )

        call_kwargs = (
            provider.client.models.generate_content.call_args
        )

        self.assertEqual(
            call_kwargs.kwargs["contents"],
            "Speak the following text in en:\n\nHello world",
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_includes_language_in_prompt(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = b"\x00\x01"

        provider.client.models.generate_content.return_value = (
            response
        )

        provider.synthesize(
            "Hello",
            language="Hindi",
        )

        call_kwargs = (
            provider.client.models.generate_content.call_args
        )

        self.assertEqual(
            call_kwargs.kwargs["contents"],
            "Speak the following text in Hindi:\n\nHello",
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_uses_default_voice(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = b"\x00\x01"

        provider.client.models.generate_content.return_value = (
            response
        )

        provider.synthesize("Hello")

        config = (
            provider.client.models.generate_content.call_args
            .kwargs["config"]
        )

        self.assertEqual(
            config.speech_config.voice_config.prebuilt_voice_config.voice_name,
            "Kore",
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_uses_custom_voice(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = b"\x00\x01"

        provider.client.models.generate_content.return_value = (
            response
        )

        provider.synthesize(
            "Hello",
            voice="Puck",
        )

        config = (
            provider.client.models.generate_content.call_args
            .kwargs["config"]
        )

        self.assertEqual(
            config.speech_config.voice_config.prebuilt_voice_config.voice_name,
            "Puck",
        )

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_empty_text(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        with self.assertRaisesMessage(
            ValueError,
            "Text cannot be empty.",
        ):
            provider.synthesize("")

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_whitespace_text(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        with self.assertRaisesMessage(
            ValueError,
            "Text cannot be empty.",
        ):
            provider.synthesize("   ")

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_wraps_provider_error(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        provider.client.models.generate_content.side_effect = (
            RuntimeError("Gemini API failed")
        )

        with self.assertRaisesMessage(
            TextToSpeechProviderError,
            "Failed to synthesize speech using Gemini.",
        ):
            provider.synthesize("Hello")

    @patch("ai.text_to_speech.gemini.genai.Client")
    def test_synthesize_wraps_empty_audio_error(
        self,
        mock_client,
    ):
        provider = GeminiTextToSpeechProvider(
            api_key="test-api-key"
        )

        response = MagicMock()
        response.candidates = [
            MagicMock()
        ]
        response.candidates[0].content.parts = [
            MagicMock()
        ]
        response.candidates[0].content.parts[
            0
        ].inline_data.data = b""

        provider.client.models.generate_content.return_value = (
            response
        )

        with self.assertRaisesMessage(
            TextToSpeechProviderError,
            "Failed to synthesize speech using Gemini.",
        ):
            provider.synthesize("Hello")

    def test_pcm_to_wav_creates_valid_wav(self):
        pcm_data = b"\x00\x01" * 50

        result = GeminiTextToSpeechProvider._pcm_to_wav(
            pcm_data
        )

        with wave.open(io.BytesIO(result), "rb") as wav_file:
            self.assertEqual(
                wav_file.getnchannels(),
                1,
            )
            self.assertEqual(
                wav_file.getsampwidth(),
                2,
            )
            self.assertEqual(
                wav_file.getframerate(),
                24000,
            )
            self.assertEqual(
                wav_file.readframes(50),
                pcm_data,
            )