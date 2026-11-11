from ai.brain.types import BrainRequest
from ai.intent.types import Intent
from ai.intent.detector import IntentDetector
from ai.intent.validator import (
    IntentValidator,
    IntentValidationResult,
)


class IntentEngine:
    """
    Detects and validates user intents before returning them.
    """

    def __init__(
        self,
        detector: IntentDetector,
        validator=None,
    ):
        self.detector = detector
        self.validator = validator or IntentValidator()

    def detect_with_validation(
        self,
        request: BrainRequest,
        *,
        context=None,
    ) -> IntentValidationResult:
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        intent = self.detector.detect(
            request,
            context=context,
        )

        if not isinstance(intent, Intent):
            raise TypeError("detector must return an Intent.")

        return self.validator.validate(intent)

    def detect(
        self,
        request: BrainRequest,
        *,
        context=None,
    ) -> Intent:
        result = self.detect_with_validation(
            request,
            context=context,
        )

        return result.intent