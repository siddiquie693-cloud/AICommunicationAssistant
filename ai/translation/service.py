from ai.translation.base import TranslationProvider

class TranslationService:
    def __init__(self, provider: TranslationProvider):
        self.provider = provider

    def translate(
        self,
        text: str,
        *,
        source_language: str | None = None,
        target_language: str,
    ) -> str:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        if not target_language or not target_language.strip():
            raise ValueError("Target language cannot be empty.")

        normalized_source_language = (
            source_language.strip()
            if source_language is not None
            else None
        )

        if normalized_source_language == "":
            raise ValueError("Source language cannot be empty.")

        return self.provider.translate(
            text.strip(),
            source_language=normalized_source_language,
            target_language=target_language.strip(),
        )