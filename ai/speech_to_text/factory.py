import os

from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.gemini import GeminiSpeechToTextProvider
from ai.speech_to_text.mock import MockSpeechToTextProvider
from ai.speech_to_text.service import SpeechToTextService


def get_speech_to_text_provider(
    provider_name: str | None = None,
) -> SpeechToTextProvider:
    if provider_name is None:
        provider_name = os.getenv(
            "SPEECH_TO_TEXT_PROVIDER",
            "mock",
        )

    provider_name = provider_name.strip().lower()

    if provider_name == "mock":
        return MockSpeechToTextProvider()

    if provider_name == "gemini":
        return GeminiSpeechToTextProvider()

    raise ValueError(
        f"Unsupported speech-to-text provider: {provider_name}"
    )


def get_speech_to_text_service(
    provider_name: str | None = None,
) -> SpeechToTextService:
    provider = get_speech_to_text_provider(provider_name)

    return SpeechToTextService(provider)