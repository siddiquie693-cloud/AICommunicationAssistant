from knowledge.services.embeddings.base import BaseEmbeddingService
from knowledge.services.vector_store.base import BaseVectorStore


class KnowledgeRetrievalService:
    """
    Retrieves relevant knowledge using embeddings and a vector store.
    """

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Retrieve the most relevant knowledge for a query.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_vector = self.embedding_service.embed(query)

        return self.vector_store.search(
            query_vector,
            top_k=top_k,
        )