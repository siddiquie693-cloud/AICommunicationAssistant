from decouple import config

from ai.providers.base import AIProvider
from ai.providers.gemini import GeminiProvider
from ai.providers.mock import MockAIProvider
from ai.providers.openai import OpenAIProvider


def get_ai_provider(
    provider_name: str | None = None,
) -> AIProvider:
    """
    Return the configured AI provider.

    If provider_name is not supplied, AI_PROVIDER is read
    from the environment configuration.

    Args:
        provider_name: Optional name of the provider to use.

    Returns:
        An initialized AIProvider implementation.

    Raises:
        ValueError: If the provider is not supported.
    """
    if provider_name is None:
        provider_name = config(
            "AI_PROVIDER",
            default="mock",
        )

    provider_name = provider_name.strip().lower()

    if provider_name == "mock":
        return MockAIProvider()

    if provider_name == "openai":
        return OpenAIProvider()

    if provider_name == "gemini":
        return GeminiProvider()

    raise ValueError(
        f"Unsupported AI provider: {provider_name}"
    )