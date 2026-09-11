from abc import ABC, abstractmethod


class TextToSpeechProvider(ABC):
    @abstractmethod
    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
    ):
        raise NotImplementedError