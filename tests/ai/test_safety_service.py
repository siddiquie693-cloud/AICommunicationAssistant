from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.safety.service import SafetyEngine
from ai.safety.types import (
    SafetyDecision,
    SafetyLevel,
    SafetyRequest,
    SafetyResult,
)


class SafetyEngineTests(SimpleTestCase):

    def test_safety_engine_delegates_evaluation_to_evaluator(self):
        evaluator = Mock()

        expected_result = SafetyResult(
            decision=SafetyDecision.ALLOW,
            reason="Action is safe.",
        )

        evaluator.evaluate.return_value = expected_result

        engine = SafetyEngine(evaluator)

        request = SafetyRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
            risk_level=SafetyLevel.LOW,
        )

        result = engine.evaluate(request)

        self.assertEqual(result, expected_result)
        evaluator.evaluate.assert_called_once_with(request)

    def test_safety_engine_rejects_non_safety_request(self):
        evaluator = Mock()
        engine = SafetyEngine(evaluator)

        with self.assertRaises(TypeError):
            engine.evaluate("open calculator")

    def test_safety_engine_rejects_invalid_evaluator_result(self):
        evaluator = Mock()
        evaluator.evaluate.return_value = "allow"

        engine = SafetyEngine(evaluator)

        request = SafetyRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
            risk_level=SafetyLevel.LOW,
        )

        with self.assertRaises(TypeError):
            engine.evaluate(request)