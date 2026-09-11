from ai.text_to_speech.base import TextToSpeechProvider
from ai.text_to_speech.mock import MockTextToSpeechProvider
from ai.text_to_speech.service import TextToSpeechService


def get_text_to_speech_provider(
    provider_name: str = "mock",
) -> TextToSpeechProvider:
    if provider_name == "mock":
        return MockTextToSpeechProvider()

    raise ValueError(
        f"Unsupported text-to-speech provider: {provider_name}"
    )


def get_text_to_speech_service(
    provider_name: str = "mock",
) -> TextToSpeechService:
    provider = get_text_to_speech_provider(provider_name)

    return TextToSpeechService(provider)