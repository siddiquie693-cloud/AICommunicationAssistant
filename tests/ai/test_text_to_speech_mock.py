from django.test import SimpleTestCase

from ai.text_to_speech.mock import MockTextToSpeechProvider


class MockTextToSpeechProviderTests(SimpleTestCase):

    def setUp(self):
        self.provider = MockTextToSpeechProvider()

    def test_synthesize_returns_mock_audio(self):
        result = self.provider.synthesize(
            "Hello world",
            language="en",
            voice="default",
        )

        self.assertEqual(
            result,
            b"Mock audio data",
        )

    def test_synthesize_without_optional_parameters(self):
        result = self.provider.synthesize(
            "Hello world",
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
            self.provider.synthesize("")

    def test_synthesize_empty_language(self):
        with self.assertRaisesMessage(
            ValueError,
            "Language cannot be empty.",
        ):
            self.provider.synthesize(
                "Hello world",
                language="",
            )

    def test_synthesize_empty_voice(self):
        with self.assertRaisesMessage(
            ValueError,
            "Voice cannot be empty.",
        ):
            self.provider.synthesize(
                "Hello world",
                voice="",
            )