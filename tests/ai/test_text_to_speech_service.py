from django.test import SimpleTestCase
from ai.text_to_speech.exceptions import TextToSpeechProviderError
from ai.text_to_speech.mock import MockTextToSpeechProvider
from ai.text_to_speech.service import TextToSpeechService


class TextToSpeechServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = TextToSpeechService(
            MockTextToSpeechProvider()
        )

    def test_synthesize(self):
        result = self.service.synthesize(
            "Hello world",
            language="en",
            voice="default",
        )

        self.assertEqual(
            result,
            b"Mock audio data",
        )

    def test_synthesize_normalizes_parameters(self):
        result = self.service.synthesize(
            "  Hello world  ",
            language=" en ",
            voice=" default ",
        )

        self.assertEqual(
            result,
            b"Mock audio data",
        )

    def test_synthesize_empty_text(self):
        with self.assertRaisesMessage(
            ValueError,
            "Text cannot be empty.",
        ):
            self.service.synthesize("")

    def test_synthesize_whitespace_text(self):
        with self.assertRaisesMessage(
            ValueError,
            "Text cannot be empty.",
        ):
            self.service.synthesize("   ")

    def test_synthesize_empty_language(self):
        with self.assertRaisesMessage(
            ValueError,
            "Language cannot be empty.",
        ):
            self.service.synthesize(
                "Hello world",
                language="",
            )

    def test_synthesize_whitespace_language(self):
        with self.assertRaisesMessage(
            ValueError,
            "Language cannot be empty.",
        ):
            self.service.synthesize(
                "Hello world",
                language="   ",
            )

    def test_synthesize_empty_voice(self):
        with self.assertRaisesMessage(
            ValueError,
            "Voice cannot be empty.",
        ):
            self.service.synthesize(
                "Hello world",
                voice="",
            )

    def test_synthesize_whitespace_voice(self):
        with self.assertRaisesMessage(
            ValueError,
            "Voice cannot be empty.",
        ):
            self.service.synthesize(
                "Hello world",
                voice="   ",
            )

    def test_synthesize_propagates_provider_error(self):
        class FailingTextToSpeechProvider:
            def synthesize(
                self,
                text,
                *,
                language=None,
                voice=None,
            ):
                raise TextToSpeechProviderError(
                    "TTS provider failed"
                )

        service = TextToSpeechService(
            FailingTextToSpeechProvider()
        )

        with self.assertRaisesMessage(
            TextToSpeechProviderError,
            "TTS provider failed",
        ):
            service.synthesize(
                "Hello world",
                language="en",
                voice="default",
            )        