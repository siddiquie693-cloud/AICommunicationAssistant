from ai.translation.base import TranslationProvider


class MockTranslationProvider(TranslationProvider):
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

        return (
            f"[{target_language}] "
            f"{text.strip()}"
        )