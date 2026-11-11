from django.test import SimpleTestCase

from ai.intent.normalizer import normalize_intent
from ai.intent.types import Intent


class IntentNormalizerTests(SimpleTestCase):
    def test_normalize_intent_strips_intent_name_whitespace(self):
        intent = Intent(
            name="  call_contact  ",
            parameters={"contact": "John"},
        )

        normalized = normalize_intent(intent)

        self.assertEqual(normalized.name, "call_contact")

    def test_normalize_intent_lowercases_intent_name(self):
        intent = Intent(
            name="CALL_CONTACT",
            parameters={"contact": "John"},
        )

        normalized = normalize_intent(intent)

        self.assertEqual(normalized.name, "call_contact")

    def test_normalize_intent_preserves_parameters(self):
        parameters = {"contact": "John", "phone": "+911234567890"}

        intent = Intent(
            name="CALL_CONTACT",
            parameters=parameters,
        )

        normalized = normalize_intent(intent)

        self.assertEqual(normalized.parameters, parameters)

    def test_normalize_intent_returns_new_intent(self):
        intent = Intent(
            name="CALL_CONTACT",
            parameters={},
        )

        normalized = normalize_intent(intent)

        self.assertIsInstance(normalized, Intent)
        self.assertIsNot(normalized, intent)

    def test_normalize_intent_rejects_invalid_input(self):
        with self.assertRaises(TypeError):
            normalize_intent("call_contact")