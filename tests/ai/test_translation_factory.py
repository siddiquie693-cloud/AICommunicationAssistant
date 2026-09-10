from unittest import TestCase

from ai.translation.factory import (
    get_translation_provider,
    get_translation_service,
)
from ai.translation.service import TranslationService
from ai.translation.mock import MockTranslationProvider

class TranslationProviderFactoryTests(TestCase):
    def test_get_mock_provider(self):
        provider = get_translation_provider("mock")

        self.assertIsInstance(
            provider,
            MockTranslationProvider,
        )

    def test_default_provider_is_mock(self):
        provider = get_translation_provider()

        self.assertIsInstance(
            provider,
            MockTranslationProvider,
        )    

    def test_unsupported_provider_raises_error(self):
        with self.assertRaises(ValueError):
            get_translation_provider("unsupported")    

    def test_get_translation_service(self):
        service = get_translation_service()

        self.assertIsInstance(
            service,
            TranslationService,
        )  

    def test_tranle_service_end_to_end(self):
        service = get_translation_service()

        result = service.translate(
            "Hello",
            source_language="en",
            target_language="fr",
        )          

        self.assertEqual(
            result,
            "[fr] Hello",
        )

    def test_translation_service_rejects_empty_text(self):
        service = get_translation_service()

        with self.assertRaises(ValueError):
            service.translate(
                "",
                target_language="fr",
            )        

    def test_translation_service_rejects_empty_target_language(self):
        service = get_translation_service()

        with self.assertRaises(ValueError):
            service.translate(
                "Hello",
                target_language="",
            )        