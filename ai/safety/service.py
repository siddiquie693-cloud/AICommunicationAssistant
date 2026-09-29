from ai.safety.types import (
    SafetyDecision,
    SafetyRequest,
    SafetyResult,
)


class SafetyEngine:
    """
    Evaluates whether a planned action can be executed.

    The Safety Engine authorizes actions but never executes them.
    """

    def __init__(self, evaluator):
        self.evaluator = evaluator

    def evaluate(
        self,
        request: SafetyRequest,
    ) -> SafetyResult:
        """
        Evaluate a safety request through the injected evaluator.
        """
        if not isinstance(request, SafetyRequest):
            raise TypeError(
                "request must be a SafetyRequest."
            )

        result = self.evaluator.evaluate(request)

        if not isinstance(result, SafetyResult):
            raise TypeError(
                "evaluator must return a SafetyResult."
            )

        return result