from ai.text_to_speech.base import TextToSpeechProvider
from ai.text_to_speech.exceptions import TextToSpeechProviderError

class MockTextToSpeechProvider(TextToSpeechProvider):
    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
    ):
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        if language is not None and not language.strip():
            raise ValueError("Language cannot be empty.")

        if voice is not None and not voice.strip():
            raise ValueError("Voice cannot be empty.")

        return b"Mock audio data"