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

        self.client = genai.Client(
            api_key=self.api_key,
        )

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
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a response using Google Gemini.
        """

        contents = self._build_contents(
            prompt,
            messages,
        )

        generation_config = self._build_config(
            system_prompt,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config,
            )
        except Exception as exc:
            raise AIProviderError(
                "Failed to generate response from Gemini."
            ) from exc

        return response.text or ""

    def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """
        Generate a response using Google Gemini as a stream.
        """

        contents = self._build_contents(
            prompt,
            messages,
        )

        generation_config = self._build_config(
            system_prompt,
        )

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
                    yield chunk.text

        except Exception as exc:
            raise AIProviderError(
                "Failed to generate streaming response from Gemini."
            ) from exc