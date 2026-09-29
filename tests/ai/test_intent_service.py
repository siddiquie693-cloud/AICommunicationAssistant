from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.intent.service import IntentEngine
from ai.intent.types import Intent


class IntentEngineTests(SimpleTestCase):

    def test_intent_engine_delegates_detection_to_detector(self):
        detector = Mock()
        expected_intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )
        detector.detect.return_value = expected_intent

        engine = IntentEngine(detector)

        request = BrainRequest(
            text="Call John",
            source="text",
            language="en",
        )

        result = engine.detect(request)

        self.assertEqual(result, expected_intent)
        detector.detect.assert_called_once_with(request)

    def test_intent_engine_rejects_non_brain_request(self):
        detector = Mock()
        engine = IntentEngine(detector)

        with self.assertRaises(TypeError):
            engine.detect("Call John")

    def test_intent_engine_rejects_invalid_detector_result(self):
        detector = Mock()
        detector.detect.return_value = "call_contact"

        engine = IntentEngine(detector)

        request = BrainRequest(
            text="Call John",
        )

        with self.assertRaises(TypeError):
            engine.detect(request)