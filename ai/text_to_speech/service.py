from ai.text_to_speech.base import TextToSpeechProvider


class TextToSpeechService:
    def __init__(self, provider: TextToSpeechProvider):
        self.provider = provider

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
    ):
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        normalized_language = (
            language.strip()
            if language is not None
            else None
        )

        if normalized_language == "":
            raise ValueError("Language cannot be empty.")

        normalized_voice = (
            voice.strip()
            if voice is not None
            else None
        )

        if normalized_voice == "":
            raise ValueError("Voice cannot be empty.")

        return self.provider.synthesize(
            text.strip(),
            language=normalized_language,
            voice=normalized_voice,
        )