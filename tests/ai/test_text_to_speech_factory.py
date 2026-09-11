from django.test import SimpleTestCase
from ai.text_to_speech.service import TextToSpeechService
from ai.text_to_speech.factory import (
    get_text_to_speech_provider,
    get_text_to_speech_service,
)
from ai.text_to_speech.mock import MockTextToSpeechProvider


class TextToSpeechFactoryTests(SimpleTestCase):

    def test_get_mock_provider(self):
        provider = get_text_to_speech_provider("mock")

        self.assertIsInstance(
            provider,
            MockTextToSpeechProvider,
        )

    def test_get_default_provider(self):
        provider = get_text_to_speech_provider()

        self.assertIsInstance(
            provider,
            MockTextToSpeechProvider,
        )

    def test_unsupported_provider(self):
        with self.assertRaisesMessage(
            ValueError,
            "Unsupported text-to-speech provider: invalid",
        ):
            get_text_to_speech_provider("invalid")

    def test_get_mock_service(self):
        service = get_text_to_speech_service("mock")

        self.assertIsInstance(
            service,
            TextToSpeechService,
        )        