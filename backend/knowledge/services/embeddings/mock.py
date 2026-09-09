from knowledge.services.embeddings.base import BaseEmbeddingService

class MockEmbeddingService(BaseEmbeddingService):
    """
    Mock embedding service used for development and testing.
    """

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        return [float(ord(char)) for char in text.strip()]