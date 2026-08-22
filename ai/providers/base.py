from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Base interface for all AI providers.

    Every provider must implement the generate method.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response from the AI provider.

        Args:
            prompt: User prompt.
            system_prompt: Optional system-level instruction.

        Returns:
            Generated text response.
        """
        raise NotImplementedError