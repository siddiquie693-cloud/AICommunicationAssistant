from ai.memory.types import MemoryQuery, MemoryResult


class MemoryEngine:
    """
    Coordinates personal-memory retrieval.

    The actual memory implementation is injected so the engine
    remains independent from storage and retrieval technology.
    """

    def __init__(self, retriever):
        self.retriever = retriever

    def retrieve(self, query: MemoryQuery) -> list[MemoryResult]:
        """
        Retrieve relevant personal memories for a query.
        """
        if not isinstance(query, MemoryQuery):
            raise TypeError("query must be a MemoryQuery.")

        results = self.retriever.retrieve(query)

        if not isinstance(results, list):
            raise TypeError("retriever must return a list.")

        if not all(
            isinstance(result, MemoryResult)
            for result in results
        ):
            raise TypeError(
                "retriever must return a list of MemoryResult objects."
            )

        return results