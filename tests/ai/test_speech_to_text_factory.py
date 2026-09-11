from django.test import SimpleTestCase
from ai.speech_to_text.exceptions import SpeechToTextProviderError
from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.factory import (
    get_speech_to_text_provider,
    get_speech_to_text_service,
)
from ai.speech_to_text.mock import MockSpeechToTextProvider
from ai.speech_to_text.service import SpeechToTextService


class SpeechToTextFactoryTests(SimpleTestCase):
    def test_get_mock_provider(self):
        provider = get_speech_to_text_provider()

        self.assertIsInstance(
            provider,
            MockSpeechToTextProvider,
        )

    def test_default_provider_is_mock(self):
        provider = get_speech_to_text_provider()

        self.assertIsInstance(
            provider,
            SpeechToTextProvider,
        )

    def test_unsupported_provider_raises_error(self):
        with self.assertRaises(ValueError):
            get_speech_to_text_provider("unsupported")

    def test_get_speech_to_text_service(self):
        service = get_speech_to_text_service()

        self.assertIsInstance(
            service,
            SpeechToTextService,
        )

    def test_speech_to_text_service_end_to_end(self):
        service = get_speech_to_text_service()

        result = service.transcribe(
            b"audio-data",
            language="en",
        )

        self.assertEqual(
            result,
            "Mock transcription",
        )    

    def test_service_propagates_provider_error(self):
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

        from ai.speech_to_text.service import SpeechToTextService

        service = SpeechToTextService(
            FailingSpeechToTextProvider()
        )

        with self.assertRaises(SpeechToTextProviderError):
            service.transcribe(
                b"audio-data",
                language="en",
            )        