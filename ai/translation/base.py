from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        *,
        source_language: str | None = None,
        target_language: str,
    ) -> str:
        raise NotImplementedError