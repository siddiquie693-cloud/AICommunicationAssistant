from ai.brain.types import BrainRequest
from ai.intent.types import Intent


class IntentEngine:
    """
    Converts a structured BrainRequest into an Intent.

    The actual intent-detection implementation is injected so that
    the Intent Engine remains independent from a specific AI provider.
    """

    def __init__(self, detector):
        self.detector = detector

    def detect(self, request: BrainRequest) -> Intent:
        """
        Detect the user's intent from a BrainRequest.
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        intent = self.detector.detect(request)

        if not isinstance(intent, Intent):
            raise TypeError("detector must return an Intent.")

        return intent