from knowledge.services.embeddings.base import BaseEmbeddingService
from knowledge.services.vector_store.base import BaseVectorStore

class KnowledgeIndexingService:
    """
    Generate embeddings for text chunks and stores them
    in the configured vector store.
    """

    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def index_chunks(self, chunks: list[str]) -> None:
        """
        Generate and store embeddings for each text chunk.
        """
        for chunk in chunks:
            if not chunk or not chunk.strip():
                raise ValueError("Chunk cannot be empty.")

            vector = self.embedding_service.embed(chunk)

            self.vector_store.add(
                vector,
                chunk.strip(),
            )    