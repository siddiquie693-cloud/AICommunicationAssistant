from ai.brain.types import BrainRequest
from ai.context.types import Context
from ai.memory.service import MemoryEngine
from ai.memory.types import MemoryQuery


class MemoryContextBuilder:
    """
    Builds personal-memory context for a NIRA Brain request.

    The memory engine is injected so this builder remains
    independent from the underlying memory storage technology.
    """

    def __init__(self, memory_engine: MemoryEngine, user_id: int):
        self.memory_engine = memory_engine
        self.user_id = user_id

    def build(self, request: BrainRequest) -> Context:
        """
        Build Context using relevant personal memories.
        """
        if not isinstance(request, BrainRequest):
            raise TypeError("request must be a BrainRequest.")

        results = self.memory_engine.retrieve(
            MemoryQuery(
                text=request.text,
                user_id=self.user_id,
            )
        )

        memory = [
            {
                "content": result.content,
                **result.metadata,
            }
            for result in results
        ]

        return Context(memory=memory)