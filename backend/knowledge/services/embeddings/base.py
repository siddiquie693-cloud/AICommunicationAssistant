from abc import ABC, abstractmethod

class BaseEmbeddingService(ABC):
    """
    Base interface for generating text embeddings.
    """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.
        """
        raise NotImplementedError