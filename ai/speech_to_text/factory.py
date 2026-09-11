from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.mock import MockSpeechToTextProvider
from ai.speech_to_text.service import SpeechToTextService


def get_speech_to_text_provider(
    provider_name: str = "mock",
) -> SpeechToTextProvider:
    if provider_name == "mock":
        return MockSpeechToTextProvider()

    raise ValueError(
        f"Unsupported speech-to-text provider: {provider_name}"
    )


def get_speech_to_text_service(
    provider_name: str = "mock",
) -> SpeechToTextService:
    provider = get_speech_to_text_provider(provider_name)

    return SpeechToTextService(provider)