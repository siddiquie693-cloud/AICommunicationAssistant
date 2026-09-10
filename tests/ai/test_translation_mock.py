from unittest import TestCase
from ai.translation.base import TranslationProvider
from ai.translation.mock import MockTranslationProvider


class MockTranslationProviderTests(TestCase):
    def setUp(self):
        self.provider = MockTranslationProvider()

    def test_translate_returns_mock_translation(self):
        result = self.provider.translate(
            "Hello",
            source_language="en",
            target_language="fr",
        )

        self.assertEqual(
            result,
            "[fr] Hello",
        )

    def test_translate_strips_text(self):
        result = self.provider.translate(
            "  Hello  ",
            target_language="hi",
        )

        self.assertEqual(
            result,
            "[hi] Hello",
        )

    def test_empty_text_raises_error(self):
        with self.assertRaises(ValueError):
            self.provider.translate(
                "",
                target_language="fr",
            )

    def test_empty_target_language_raises_error(self):
        with self.assertRaises(ValueError):
            self.provider.translate(
                "Hello",
                target_language="",
            )

    def test_translate_accepts_source_language(self):
        result = self.provider.translate(
            "Hello",
            source_language="en",
            target_language="fr",
        )        

        self.assertEqual(
            result,
            "[fr] Hello",
        )

    def test_provider_implements_translation_provider(self):
        self.assertIsInstance(
            self.provider,
            TranslationProvider,
        )    