from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.intent.service import IntentEngine
from ai.intent.types import Intent


class IntentEngineTests(SimpleTestCase):
    def test_intent_engine_accepts_brain_request_and_returns_intent(self):
        request = BrainRequest(
            text="Call John",
            source="text",
        )

        intent = Intent(
            name="call_person",
            parameters={"recipient": "John"},
        )

        detector = Mock()
        detector.detect.return_value = intent

        engine = IntentEngine(detector)

        result = engine.detect(request)

        self.assertIs(result, intent)
        detector.detect.assert_called_once_with(
            request,
            context=None,
        )

    def test_intent_engine_rejects_invalid_request(self):
        detector = Mock()
        engine = IntentEngine(detector)

        with self.assertRaises(TypeError):
            engine.detect("Call John")

        detector.detect.assert_not_called()

    def test_intent_engine_rejects_invalid_detector_result(self):
        request = BrainRequest(
            text="Call John",
            source="text",
        )

        detector = Mock()
        detector.detect.return_value = {
            "name": "call_person",
            "parameters": {"recipient": "John"},
        }

        engine = IntentEngine(detector)

        with self.assertRaisesRegex(
            TypeError,
            "detector must return an Intent.",
        ):
            engine.detect(request)

    def test_intent_engine_preserves_detector_intent_parameters(self):
        request = BrainRequest(
            text="Send John a message saying I will call later",
            source="text",
        )

        intent = Intent(
            name="send_message",
            parameters={
                "recipient": "John",
                "message": "I will call later",
            },
        )

        detector = Mock()
        detector.detect.return_value = intent

        engine = IntentEngine(detector)

        result = engine.detect(request)

        self.assertEqual(result.name, "send_message")
        self.assertEqual(
            result.parameters,
            {
                "recipient": "John",
                "message": "I will call later",
            },
        )