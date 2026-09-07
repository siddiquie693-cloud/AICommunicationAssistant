from ai.providers.base import AIProvider
from ai.prompts.manager import PromptManager

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
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate an AI response through the configured provider.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if system_prompt is None:
            PromptManager.validate_system_prompts()
            system_prompt = (
                PromptManager.get_conversation_system_prompt()
            )

        return self.provider.generate(
            prompt.strip(),
            system_prompt=system_prompt,
            messages=messages,
        )

    def generate_stream(
            self,
            prompt: str,
            *,
            system_prompt: str | None = None,
            messages: list[dict[str, str]] | None = None,
    ):
        """
        Generate an AI response as a stream of text chunks.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if system_prompt is None:
            PromptManager.validate_system_prompts()
            system_prompt = (
                PromptManager.get_conversation_system_prompt()
            )

        return self.provider.generate_stream(
            prompt.strip(),
            system_prompt=system_prompt,
            messages=messages,
        )    