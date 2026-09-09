from ai.retrieval.base import BaseRetriever
from ai.retrieval.types import RetrievalResult

class MockRetriever(BaseRetriever):
    """
    Mock retriever used for development and testing.
    """

    def __init__(self, documents: list[str] | None = None):
        self.documents = documents or []

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if top_k <=0:
            raise ValueError("top_k must be greater than zero.")

        return [
            RetrievalResult(
                content=document,
                score=1.0,
            )
            for document in self.documents[:top_k]
        ]   