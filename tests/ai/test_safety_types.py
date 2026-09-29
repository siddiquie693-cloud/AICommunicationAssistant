from django.test import SimpleTestCase

from ai.safety.types import (
    SafetyDecision,
    SafetyLevel,
    SafetyRequest,
    SafetyResult,
)


class SafetyRequestTests(SimpleTestCase):

    def test_safety_request_stores_all_fields(self):
        request = SafetyRequest(
            action_name="send_message",
            parameters={
                "recipient": "+911234567890",
                "content": "Hello",
            },
            risk_level=SafetyLevel.MEDIUM,
        )

        self.assertEqual(
            request.action_name,
            "send_message",
        )
        self.assertEqual(
            request.parameters,
            {
                "recipient": "+911234567890",
                "content": "Hello",
            },
        )
        self.assertEqual(
            request.risk_level,
            SafetyLevel.MEDIUM,
        )


class SafetyResultTests(SimpleTestCase):

    def test_safety_result_stores_decision_and_reason(self):
        result = SafetyResult(
            decision=SafetyDecision.CONFIRM,
            reason="User confirmation is required.",
        )

        self.assertEqual(
            result.decision,
            SafetyDecision.CONFIRM,
        )
        self.assertEqual(
            result.reason,
            "User confirmation is required.",
        )


class SafetyLevelTests(SimpleTestCase):

    def test_safety_levels_have_expected_values(self):
        self.assertEqual(SafetyLevel.LOW.value, "low")
        self.assertEqual(SafetyLevel.MEDIUM.value, "medium")
        self.assertEqual(SafetyLevel.HIGH.value, "high")


class SafetyDecisionTests(SimpleTestCase):

    def test_safety_decisions_have_expected_values(self):
        self.assertEqual(SafetyDecision.ALLOW.value, "allow")
        self.assertEqual(SafetyDecision.CONFIRM.value, "confirm")
        self.assertEqual(SafetyDecision.DENY.value, "deny")