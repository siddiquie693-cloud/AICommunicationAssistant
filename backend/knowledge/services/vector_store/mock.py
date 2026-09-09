from knowledge.services.vector_store.base import BaseVectorStore

class MockVectorStore(BaseVectorStore):
    """
    In-memory vector store used for development and testing.
    """

    def __init__(self):
        self._items: list[tuple[list[float], str]] = []

    def add(
        self,
        vector: list[float],
        content: str,
    ) -> None:
        if not vector:
            raise ValueError("Vector cannot be empty.")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        self._items.append(
            (vector, content.strip()),
        )

    def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        if not vector:
            raise ValueError("Vector cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        results = []

        for stored_vector, content in self._items:
            score = self._similarity(vector, stored_vector)
            results.append((content, score))

        results.sort(
            key=lambda item: item[1],
            reverse=True,
        )    

        return results[:top_k]

    @staticmethod
    def _similarity(
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        if len(vector_a) != len(vector_b):
            raise ValueError("Vector must have the same dimensions.")

        dot_product = sum(
            a * b 
            for a, b in zip(vector_a, vector_b)
        )

        magnitude_a = sum(a *a for a in vector_a) ** 0.5
        magnitude_b = sum(b * b for b in vector_b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)