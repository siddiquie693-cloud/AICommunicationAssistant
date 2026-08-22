from django.test import SimpleTestCase

from ai.providers.mock import MockAIProvider
from ai.services.ai_service import AIService


class AIServiceTests(SimpleTestCase):

    def setUp(self):
        self.provider = MockAIProvider()
        self.service = AIService(self.provider)

    def test_generate_response(self):
        response = self.service.generate_response(
            "Hello AI"
        )

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_response_strips_prompt(self):
        response = self.service.generate_response(
            "  Hello AI  "
        )

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_empty_prompt_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.generate_response("")