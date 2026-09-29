from ai.brain.types import BrainPipelineResult, BrainRequest


class NIRACore:
    """
    Application-level entry point for NIRA AI.
    """

    def __init__(self, brain):
        if brain is None:
            raise ValueError(
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
            raise TypeError(
                "request must be a BrainRequest."
            )

        result = self.brain.process(request)

        if not isinstance(result, BrainPipelineResult):
            raise TypeError(
                "brain.process() must return a BrainPipelineResult."
            )
        return result