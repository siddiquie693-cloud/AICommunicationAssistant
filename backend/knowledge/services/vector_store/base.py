from abc import ABC, abstractmethod

class BaseVectorStore(ABC):
    """
    Base interface for storing and searching embedding vectors.
    """

    @abstractmethod
    def add(
        self,
        vector: list[float],
        content: str,
    ) -> None:
        """
        Store an embedding vector with its content.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        vector: list[float],
        *,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Search for the most relevant stored vectors.
        """
        raise NotImplementedError