from ai.providers.base import AIProvider


class MockAIProvider(AIProvider):
    """
    Mock AI provider used for development and testing.

    This provider does not call an external AI service.
    """

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Return a deterministic mock response.
        """
        return f"Mock AI response: {prompt}"