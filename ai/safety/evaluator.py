
from ai.safety.types import (
    SafetyDecision,
    SafetyLevel,
    SafetyRequest,
    SafetyResult,
)


class RuleBasedSafetyEvaluator:
    """
    Deterministic, fail-closed safety policy for NIRA.

    The evaluator does not use profile instructions or LLM output
    to authorize actions.
    """

    ACTION_RISK_MAPPING = {
        "open_app": SafetyLevel.LOW,
        "navigate": SafetyLevel.LOW,
        "play_media": SafetyLevel.LOW,
        "create_reminder": SafetyLevel.MEDIUM,
        "send_message": SafetyLevel.HIGH,
        "call_person": SafetyLevel.HIGH,
    }

    def evaluate(self, request: SafetyRequest) -> SafetyResult:
        if not isinstance(request, SafetyRequest):
            raise TypeError(
                "request must be a SafetyRequest."
            )

        if (
            not isinstance(request.action_name, str)
            or not request.action_name.strip()
            or not isinstance(request.parameters, dict)
        ):
            return SafetyResult(
                decision=SafetyDecision.DENY,
                reason="Invalid safety request.",
            )

        expected_risk = self.ACTION_RISK_MAPPING.get(
            request.action_name
        )

        if expected_risk is None:
            return SafetyResult(
                decision=SafetyDecision.DENY,
                reason="Unsupported action.",
            )

        if request.risk_level != expected_risk:
            return SafetyResult(
                decision=SafetyDecision.DENY,
                reason="Action risk classification mismatch.",
            )

        if expected_risk == SafetyLevel.LOW:
            return SafetyResult(
                decision=SafetyDecision.ALLOW,
                reason="Action is classified as low risk.",
            )

        return SafetyResult(
            decision=SafetyDecision.CONFIRM,
            reason="User confirmation is required.",
        )