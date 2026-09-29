from ai.brain.types import BrainPipelineResult, BrainRequest
from ai.core.exceptions import (
    NIRACoreProcessingError,
    NIRACoreValidationError,
)
import logging

logger = logging.getLogger(__name__)

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

        logger.info(
            "NIRA Core processing request from source=%s",
            request.source,
        )

        try:
            result = self.brain.process(request)
        except NIRACoreProcessingError:
            logger.exception(
                "NIRA Core processing failed with a Core processing error."
            )
            raise
        except Exception:
            logger.exception(
                "NIRA Core processing failed with an unexpected error."
            )
            raise

        if not isinstance(result, BrainPipelineResult):
            raise NIRACoreProcessingError(
                "brain.process() must return a BrainPipelineResult."
            )

        logger.info(
            "NIRA Core processing completed successfully.",
        )

        return result