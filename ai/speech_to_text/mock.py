from ai.speech_to_text.base import SpeechToTextProvider
from ai.speech_to_text.exceptions import SpeechToTextProviderError

class MockSpeechToTextProvider(SpeechToTextProvider):
    def transcribe(
        self,
        audio,
        *,
        language: str | None = None,
    ) -> str:
        if audio is None:
            raise ValueError("Audio cannot be empty.")

        if language is not None and not language.strip():
            raise ValueError("Language cannot be empty.")

        return "Mock transcription"