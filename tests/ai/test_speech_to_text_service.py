from django.test import SimpleTestCase
from ai.speech_to_text.exceptions import SpeechToTextProviderError
from ai.speech_to_text.mock import MockSpeechToTextProvider
from ai.speech_to_text.service import SpeechToTextService


class SpeechToTextServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = SpeechToTextService(
            MockSpeechToTextProvider()
        )

    def test_transcribe_delegates_to_provider(self):
        result = self.service.transcribe(
            b"audio-data",
            language="en",
        )

        self.assertEqual(
            result,
            "Mock transcription",
        )

    def test_transcribe_strips_language(self):
        result = self.service.transcribe(
            b"audio-data",
            language=" en ",
        )

        self.assertEqual(
            result,
            "Mock transcription",
        )

    def test_transcribe_rejects_empty_audio(self):
        with self.assertRaises(ValueError):
            self.service.transcribe(
                None,
                language="en",
            )

    def test_transcribe_rejects_empty_language(self):
        with self.assertRaises(ValueError):
            self.service.transcribe(
                b"audio-data",
                language="   ",
            )

    def test_transcribe_propagates_provider_error(self):
        class FailingSpeechToTextProvider:
            def transcribe(
                self,
                audio,
                *,
                language=None,
            ):
                raise SpeechToTextProviderError(
                    "STT provider failed"
                )

        service = SpeechToTextService(
            FailingSpeechToTextProvider()
        )

        with self.assertRaises(SpeechToTextProviderError):
            service.transcribe(
                b"audio-data",
                language="en",
            )        