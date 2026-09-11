from django.test import SimpleTestCase
from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.mock import MockSpeechToTextProvider


class MockSpeechToTextProviderTests(SimpleTestCase):
    def setUp(self):
        self.provider = MockSpeechToTextProvider()

    def test_transcribe_returns_mock_text(self):
        result = self.provider.transcribe(
            b"audio-data",
            language="en",
        )

        self.assertEqual(
            result,
            "Mock transcription",
        )

    def test_transcribe_accepts_audio_object(self):
        audio = object()

        result = self.provider.transcribe(
            audio,
            language="en",
        )

        self.assertEqual(
            result,
            "Mock transcription",
        )

    def test_transcribe_rejects_empty_audio(self):
        with self.assertRaises(ValueError):
            self.provider.transcribe(
                None,
                language="en",
            )

    def test_transcribe_rejects_empty_language(self):
        with self.assertRaises(ValueError):
            self.provider.transcribe(
                b"audio-data",
                language="   ",
            )

    def test_provider_implements_speech_to_text_provider(self):
        self.assertIsInstance(
            self.provider,
            SpeechToTextProvider,
        )        