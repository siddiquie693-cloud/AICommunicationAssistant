from ai.providers.base import AIProvider
from ai.providers.mock import MockAIProvider
from ai.providers.openai import OpenAIProvider

def get_ai_provider(provider_name: str = "mock") -> AIProvider:
    """
    Return the configured AI provider.

    Args:
        provider_name: Name of the provider to use.

    Returns:
        An initialized AIProvider implementation.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider_name = provider_name.strip().lower()

    if provider_name == "mock":
        return MockAIProvider()

    if provider_name == "openai":
        return OpenAIProvider()

    raise ValueError(
        f"Unsupported AI provider: {provider_name}"
    )