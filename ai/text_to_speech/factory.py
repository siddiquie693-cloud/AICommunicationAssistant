import os

from ai.text_to_speech.base import TextToSpeechProvider
from ai.text_to_speech.gemini import GeminiTextToSpeechProvider
from ai.text_to_speech.mock import MockTextToSpeechProvider
from ai.text_to_speech.service import TextToSpeechService


def get_text_to_speech_provider(
    provider_name: str | None = None,
) -> TextToSpeechProvider:
    provider_name = (
        provider_name
        or os.getenv(
            "TEXT_TO_SPEECH_PROVIDER",
            "gemini",
        )
    ).lower()

    if provider_name == "mock":
        return MockTextToSpeechProvider()

    if provider_name == "gemini":
        return GeminiTextToSpeechProvider()

    raise ValueError(
        f"Unsupported text-to-speech provider: {provider_name}"
    )


def get_text_to_speech_service(
    provider_name: str | None = None,
) -> TextToSpeechService:
    provider = get_text_to_speech_provider(
        provider_name
    )

    return TextToSpeechService(provider)