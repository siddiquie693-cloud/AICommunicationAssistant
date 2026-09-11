from ai.speech_to_text.base import SpeechToTextProvider


class SpeechToTextService:
    def __init__(self, provider: SpeechToTextProvider):
        self.provider = provider

    def transcribe(
        self,
        audio,
        *,
        language: str | None = None,
    ) -> str:
        if audio is None:
            raise ValueError("Audio cannot be empty.")

        normalized_language = (
            language.strip()
            if language is not None
            else None
        )

        if normalized_language == "":
            raise ValueError("Language cannot be empty.")

        return self.provider.transcribe(
            audio,
            language=normalized_language,
        )