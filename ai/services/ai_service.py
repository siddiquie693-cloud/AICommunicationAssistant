from ai.providers.base import AIProvider


class AIService:
    """
    Application-level service responsible for interacting
    with an AI provider.
    """

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def generate_response(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate an AI response through the configured provider.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        return self.provider.generate(
            prompt.strip(),
            system_prompt=system_prompt,
        )