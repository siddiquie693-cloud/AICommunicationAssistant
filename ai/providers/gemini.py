
import time
from collections.abc import Iterator

from decouple import config
from google import genai
from google.genai import types

from ai.providers.base import AIProvider
from ai.providers.exceptions import AIProviderError


class GeminiProvider(AIProvider):
    """
    AI provider implementation using Google Gemini.
    """

    def __init__(self):
        self.api_key = config(
            "GEMINI_API_KEY",
            default="",
        )

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = config(
            "GEMINI_MODEL",
            default="gemini-2.5-flash",
        )

        self.temperature = config(
            "GEMINI_TEMPERATURE",
            default=0.7,
            cast=float,
        )

        self.max_tokens = config(
            "GEMINI_MAX_TOKENS",
            default=1000,
            cast=int,
        )

        self.thinking_budget = config(
            "GEMINI_THINKING_BUDGET",
            default=0,
            cast=int,
        )

        self.max_retries = config(
            "GEMINI_MAX_RETRIES",
            default=2,
            cast=int,
        )

        self.retry_base_delay = config(
            "GEMINI_RETRY_BASE_DELAY",
            default=1.0,
            cast=float,
        )

        self.client = genai.Client(
            api_key=self.api_key,
        )

    def _is_retryable_error(self, exc: Exception) -> bool:
        """
        Identify temporary Gemini API errors.
        """

        status_codes = [
            getattr(exc, "code", None),
            getattr(exc, "status_code", None),
        ]

        response = getattr(exc, "response", None)

        if response is not None:
            status_codes.append(
                getattr(response, "status_code", None)
            )

        for status in status_codes:
            try:
                if int(status) in (429, 503):
                    return True
            except (TypeError, ValueError):
                continue

        error_text = str(exc).upper()

        retryable_markers = (
            "429",
            "503",
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
            "TOO MANY REQUESTS",
            "SERVICE UNAVAILABLE",
        )

        return any(
            marker in error_text
            for marker in retryable_markers
        )

    def _retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential retry delay.
        """

        return self.retry_base_delay * (2 ** attempt)

    def _build_contents(
        self,
        prompt: str,
        messages: list[dict[str, str]] | None = None,
    ) -> list[types.Content]:

        contents = []

        if messages is not None:
            for message in messages:
                role = message.get("role", "user")

                if role == "assistant":
                    role = "model"

                contents.append(
                    types.Content(
                        role=role,
                        parts=[
                            types.Part.from_text(
                                text=message.get("content", "")
                            )
                        ],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=prompt
                    )
                ],
            )
        )

        return contents

    def _build_config(
        self,
        system_prompt: str | None = None,
    ) -> types.GenerateContentConfig:

        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=self.thinking_budget,
            ),
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a response with retry handling.
        """

        contents = self._build_contents(
            prompt,
            messages,
        )

        generation_config = self._build_config(
            system_prompt,
        )

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=generation_config,
                )

                return response.text or ""

            except Exception as exc:
                should_retry = (
                    self._is_retryable_error(exc)
                    and attempt < self.max_retries
                )

                if should_retry:
                    delay = self._retry_delay(attempt)
                    time.sleep(delay)
                    continue

                raise AIProviderError(
                    "Failed to generate response from Gemini."
                ) from exc

        raise AIProviderError(
            "Failed to generate response from Gemini."
        )

    def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """
        Generate a streaming response.

        Retries temporary errors only before the first
        response chunk is delivered.
        """

        contents = self._build_contents(
            prompt,
            messages,
        )

        generation_config = self._build_config(
            system_prompt,
        )

        for attempt in range(self.max_retries + 1):
            response_started = False

            try:
                response_stream = (
                    self.client.models.generate_content_stream(
                        model=self.model,
                        contents=contents,
                        config=generation_config,
                    )
                )

                for chunk in response_stream:
                    if chunk.text:
                        response_started = True
                        yield chunk.text

                return

            except Exception as exc:
                should_retry = (
                    not response_started
                    and self._is_retryable_error(exc)
                    and attempt < self.max_retries
                )

                if should_retry:
                    delay = self._retry_delay(attempt)
                    time.sleep(delay)
                    continue

                print(
                    "GEMINI STREAM ERROR:",
                    repr(exc),
                )

                raise AIProviderError(
                    "Failed to generate streaming response from Gemini."
                ) from exc

        raise AIProviderError(
            "Failed to generate streaming response from Gemini."
        )