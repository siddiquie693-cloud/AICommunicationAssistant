from django.test import SimpleTestCase

from ai.intent.types import Intent


class IntentTests(SimpleTestCase):

    def test_intent_stores_name_and_parameters(self):
        intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )

        self.assertEqual(intent.name, "call_contact")
        self.assertEqual(
            intent.parameters,
            {"contact": "John"},
        )

    def test_intent_accepts_empty_parameters(self):
        intent = Intent(
            name="open_app",
            parameters={},
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(intent.parameters, {})

    def test_intent_rejects_non_string_name(self):
        with self.assertRaises(TypeError):
            Intent(
                name=123,
                parameters={},
            )

    def test_intent_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Intent(
                name="",
                parameters={},
            )

    def test_intent_rejects_whitespace_only_name(self):
        with self.assertRaises(ValueError):
            Intent(
                name="   ",
                parameters={},
            )

    def test_intent_rejects_non_dictionary_parameters(self):
        with self.assertRaises(TypeError):
            Intent(
                name="call_contact",
                parameters=[],
            )

    def test_intent_is_immutable(self):
        intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )

        with self.assertRaises(AttributeError):
            intent.name = "send_message"
