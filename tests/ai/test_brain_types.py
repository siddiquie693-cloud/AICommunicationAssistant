from django.test import SimpleTestCase

from ai.brain.types import BrainRequest


class BrainRequestTests(SimpleTestCase):

    def test_brain_request_stores_text_source_and_language(self):
        request = BrainRequest(
            text="Call John",
            source="voice",
            language="en",
        )

        self.assertEqual(request.text, "Call John")
        self.assertEqual(request.source, "voice")
        self.assertEqual(request.language, "en")

    def test_brain_request_uses_text_as_default_source(self):
        request = BrainRequest(
            text="Hello",
        )

        self.assertEqual(request.source, "text")
        self.assertIsNone(request.language)