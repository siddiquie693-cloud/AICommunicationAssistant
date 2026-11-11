from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.intent.categories import IntentCategory
from ai.intent.detector import BasicIntentDetector, IntentDetector
from ai.intent.normalizer import normalize_intent
from ai.intent.service import IntentEngine
from ai.intent.types import Intent
from ai.intent.unknown import create_unknown_intent


class IntentFoundationTests(SimpleTestCase):
    def test_intent_categories_are_available(self):
        self.assertEqual(
            IntentCategory.COMMUNICATION.value,
            "communication",
        )
        self.assertEqual(
            IntentCategory.PHONE.value,
            "phone",
        )
        self.assertEqual(
            IntentCategory.MESSAGING.value,
            "messaging",
        )
        self.assertEqual(
            IntentCategory.UNKNOWN.value,
            "unknown",
        )

    def test_intent_contract_accepts_valid_data(self):
        intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )

        self.assertEqual(intent.name, "call_contact")
        self.assertEqual(
            intent.parameters,
            {"contact": "John"},
        )

    def test_intent_contract_rejects_invalid_name(self):
        with self.assertRaises(TypeError):
            Intent(
                name=123,
                parameters={},
            )

    def test_intent_contract_rejects_invalid_parameters(self):
        with self.assertRaises(TypeError):
            Intent(
                name="call_contact",
                parameters=[],
            )

    def test_unknown_intent_factory_returns_unknown_intent(self):
        intent = create_unknown_intent()

        self.assertEqual(
            intent.name,
            IntentCategory.UNKNOWN.value,
        )
        self.assertEqual(intent.parameters, {})

    def test_intent_normalization_normalizes_name(self):
        intent = Intent(
            name="  CALL_CONTACT  ",
            parameters={"contact": "John"},
        )

        normalized = normalize_intent(intent)

        self.assertEqual(normalized.name, "call_contact")
        self.assertEqual(
            normalized.parameters,
            {"contact": "John"},
        )

    def test_basic_intent_detector_implements_contract(self):
        detector = BasicIntentDetector()

        self.assertIsInstance(
            detector,
            IntentDetector,
        )

    def test_basic_intent_detector_returns_unknown_intent(self):
        detector = BasicIntentDetector()

        intent = detector.detect(
            BrainRequest(text="hello"),
        )

        self.assertEqual(
            intent.name,
            IntentCategory.UNKNOWN.value,
        )

    def test_intent_engine_uses_basic_intent_detector(self):
        detector = BasicIntentDetector()
        engine = IntentEngine(detector)

        intent = engine.detect(
            BrainRequest(text="hello"),
        )

        self.assertIsInstance(intent, Intent)
        self.assertEqual(
            intent.name,
            IntentCategory.UNKNOWN.value,
        )

    def test_intent_engine_preserves_detector_parameters(self):
        class FixedIntentDetector(IntentDetector):
            def detect(self, request, *, context=None):
                return Intent(
                    name="call_contact",
                    parameters={"contact": "John"},
                )

        engine = IntentEngine(
            FixedIntentDetector(),
        )

        intent = engine.detect(
            BrainRequest(text="call John"),
        )

        self.assertEqual(intent.name, "call_contact")
        self.assertEqual(
            intent.parameters,
            {"contact": "John"},
        )