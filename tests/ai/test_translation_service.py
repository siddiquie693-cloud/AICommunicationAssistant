from unittest import TestCase
from unittest.mock import Mock
from ai.translation.mock import MockTranslationProvider
from ai.translation.service import TranslationService

from ai.translation.service import TranslationService

class TranslationServiceTests(TestCase):
    def test_translate_delegates_to_provider(self):
        provider = Mock()
        provider.translate.return_value = "[fr] Hello"

        service = TranslationService(provider)

        result = service.translate(
            "Hello",
            source_language="en",
            target_language="fr",
        )

        self.assertEqual(result, "[fr] Hello")

        provider.translate.assert_called_once_with(
            "Hello",
            source_language="en",
            target_language="fr",
        )

    def test_translate_strips_text_and_target_language(self):
        provider = Mock()
        provider.transalte.return_value = "[hi] Hello"

        service = TranslationService(provider)

        service.translate(
            " Hello ",
            target_language="  hi  ",
        )    

        provider.translate.assert_called_once_with(
            "Hello",
            source_language=None,
            target_language="hi",
        )

    def test_empty_text_raises_error(self):
        provider = Mock()
        service = TranslationService(provider)

        with self.assertRaises(ValueError):
            service.translate(
                "",
                target_language="fr",
            )    

        provider.translate.assert_not_called()

    def test_empty_target_language_raises_error(self):
        provider = Mock()
        service = TranslationService(provider)

        with self.assertRaises(ValueError):
            service.translate(
                "Hello",
                target_language="",
            )        

        provider.translate.assert_not_called()  

    def test_source_language_is_stripped(self):
        service = TranslationService(
            MockTranslationProvider()
        )

        result = service.translate(
            "Hello",
            source_language=" en ",
            target_language=" fr ",
        )      

        self.assertEqual(result, "[fr] Hello")

    def test_empty_source_language_raises_error(self):
        service = TranslationService(
            MockTranslationProvider()
        )

        with self.assertRaises(ValueError):
            service.translate(
                "Hello",
                source_language="  ",
                target_language="fr",
            )    