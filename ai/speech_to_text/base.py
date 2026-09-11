from abc import ABC, abstractmethod


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(
        self,
        audio,
        *,
        language: str | None = None,
    ) -> str:
        raise NotImplementedError