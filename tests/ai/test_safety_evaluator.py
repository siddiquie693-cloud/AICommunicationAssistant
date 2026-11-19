
from django.test import SimpleTestCase

from ai.safety.evaluator import RuleBasedSafetyEvaluator
from ai.safety.types import (
    SafetyDecision,
    SafetyLevel,
    SafetyRequest,
)


class RuleBasedSafetyEvaluatorTests(SimpleTestCase):

    def setUp(self):
        self.evaluator = RuleBasedSafetyEvaluator()

    def test_allows_low_risk_open_app_action(self):
        request = SafetyRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.ALLOW)

    def test_allows_low_risk_navigation_action(self):
        request = SafetyRequest(
            action_name="navigate",
            parameters={"location": "Bhopal"},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.ALLOW)

    def test_allows_low_risk_play_media_action(self):
        request = SafetyRequest(
            action_name="play_media",
            parameters={"request": "play music"},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.ALLOW)

    def test_requires_confirmation_for_medium_risk_action(self):
        request = SafetyRequest(
            action_name="create_reminder",
            parameters={"request": "Remind me tomorrow"},
            risk_level=SafetyLevel.MEDIUM,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.CONFIRM)

    def test_requires_confirmation_for_high_risk_message(self):
        request = SafetyRequest(
            action_name="send_message",
            parameters={
                "recipient": "John",
                "content": "Hello",
            },
            risk_level=SafetyLevel.HIGH,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.CONFIRM)

    def test_requires_confirmation_for_high_risk_call(self):
        request = SafetyRequest(
            action_name="call_person",
            parameters={"recipient": "John"},
            risk_level=SafetyLevel.HIGH,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.CONFIRM)

    def test_denies_unsupported_action(self):
        request = SafetyRequest(
            action_name="delete_account",
            parameters={},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_denies_action_with_mismatched_risk_level(self):
        request = SafetyRequest(
            action_name="send_message",
            parameters={"recipient": "John"},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_rejects_non_safety_request(self):
        with self.assertRaises(TypeError):
            self.evaluator.evaluate("send a message")

    def test_denies_invalid_action_name(self):
        request = SafetyRequest(
            action_name=" ",
            parameters={},
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.DENY)

    def test_denies_invalid_parameters(self):
        request = SafetyRequest(
            action_name="open_app",
            parameters=None,
            risk_level=SafetyLevel.LOW,
        )

        result = self.evaluator.evaluate(request)

        self.assertEqual(result.decision, SafetyDecision.DENY)