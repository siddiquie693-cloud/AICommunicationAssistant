from ai.brain.types import BrainRequest
from ai.context.types import Context


class ContextEngine:
    """
    Builds structured context for a NIRA Brain request.

    Context sources are injected so this engine remains independent
    from specific memory, knowledge, profile, or conversation storage.
    """

    def __init__(self, builder):
        self.builder = builder

    def build(self, request: BrainRequest) -> Context:
        """
        Build context from a BrainRequest.
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        context = self.builder.build(request)

        if not isinstance(context, Context):
            raise TypeError("builder must return a Context.")

        return context