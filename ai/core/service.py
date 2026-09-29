from ai.brain.types import BrainPipelineResult, BrainRequest
from ai.core.exceptions import (
    NIRACoreProcessingError,
    NIRACoreValidationError,
)


class NIRACore:
    """
    Application-level entry point for NIRA AI.
    """

    def __init__(self, brain):
        if brain is None:
            raise NIRACoreValidationError(
                "brain must be provided."
            )

        self.brain = brain

    def process(
        self,
        request: BrainRequest,
    ) -> BrainPipelineResult:
        """
        Process a user request through the NIRA Brain.
        """
        if not isinstance(request, BrainRequest):
            raise NIRACoreValidationError(
                "request must be a BrainRequest."
            )

        try:
            result = self.brain.process(request)
        except NIRACoreProcessingError:
            raise
        except Exception:
            raise

        if not isinstance(result, BrainPipelineResult):
            raise NIRACoreProcessingError(
                "brain.process() must return a BrainPipelineResult."
            )

        return result