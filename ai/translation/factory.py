from ai.translation.mock import MockTranslationProvider
from ai.translation.service import TranslationService


def get_translation_provider(
    provider_name: str = "mock",
):
    if provider_name == "mock":
        return MockTranslationProvider()

    raise ValueError(
        f"Unsupported translation provider: {provider_name}"
    )


def get_translation_service(
    provider_name: str = "mock",
) -> TranslationService:
    provider = get_translation_provider(provider_name)

    return TranslationService(provider)