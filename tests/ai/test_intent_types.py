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