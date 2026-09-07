from abc import ABC, abstractmethod
from collections.abc import Iterator

class AIProvider(ABC):
    """
    Base interface for all AI providers.

    Every provider must implement the generate and generate_stream methods.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a response from the AI provider.

        Args:
            prompt: User prompt.
            system_prompt: Optional system-level instruction.
            messages: Optional conversation history.

        Returns:
            Generated text response.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """
        Generate a response as a stream of text chunks.

        Args:
            prompt: User prompt.
            system_prompt: Optional system-level instruction.
            messages: Optional conversation history.

        Yields:
            Individual response text chunks.
        """
        raise NotImplementedError