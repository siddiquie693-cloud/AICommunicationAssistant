from ai.brain.types import BrainPipelineResult, BrainRequest


class NIRACore:
    """
    Application-level entry point for NIRA AI.
    """

    def __init__(self, brain):
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

        return self.brain.process(request)