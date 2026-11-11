from django.test import SimpleTestCase

from ai.intent.categories import IntentCategory
from ai.intent.unknown import create_unknown_intent
from ai.intent.types import Intent


class UnknownIntentTests(SimpleTestCase):
    def test_create_unknown_intent_returns_intent(self):
        intent = create_unknown_intent()

        self.assertIsInstance(intent, Intent)

    def test_create_unknown_intent_uses_unknown_category(self):
        intent = create_unknown_intent()

        self.assertEqual(
            intent.name,
            IntentCategory.UNKNOWN.value,
        )

    def test_create_unknown_intent_has_empty_parameters(self):
        intent = create_unknown_intent()

        self.assertEqual(intent.parameters, {})