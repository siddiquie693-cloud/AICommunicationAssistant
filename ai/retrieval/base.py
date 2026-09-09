from abc import ABC, abstractmethod
from ai.retrieval.types import RetrievalResult

class BaseRetriever(ABC):
    """
    Base interface for knowledge retrieval.

    Implementations are responsible for finding relevant
    knowledge based on a user query.
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant knowledge for a query.

        Args:
            query: User's search/query text.
            top_k: Maximum number of results to return.

        Returns:
            A list of relevant text passages.
        """
        raise NotImplementedError