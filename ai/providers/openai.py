from decouple import config
from openai import OpenAI

from ai.providers.base import AIProvider
from ai.providers.exceptions import AIProviderError


class OpenAIProvider(AIProvider):
    """
    AI provider implementation using OpenAI.
    """

    def __init__(self):
        self.api_key = config(
            "OPENAI_API_KEY",
            default="",
        )

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = config(
            "OPENAI_MODEL",
            default="gpt-4o-mini",
        )

        self.temperature = config(
            "OPENAI_TEMPERATURE",
            default=0.7,
            cast=float,
        )

        self.max_tokens = config(
            "OPENAI_MAX_TOKENS",
            default=1000,
            cast=int,
        )

        self.timeout = config(
            "OPENAI_TIMEOUT",
            default=30,
            cast=int,
        )

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a response using OpenAI.
        """

        request_messages = []

        if system_prompt:
            request_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        if messages is not None:
            request_messages.extend(messages)
            
        request_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=request_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise AIProviderError(
                "Failed to generate response from OpenAI."
            ) from exc

        return response.choices[0].message.content or ""

    def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ):
        """
        Generate a response using OpenAI as a stream.
        """

        request_messages = []

        if system_prompt:
            request_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        if messages is not None:
            request_messages.extend(messages)

        request_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        try:
            response_stream = self.client.chat.completions.create(
                model=self.model,
                messages=request_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )

            for chunk in response_stream:
                content = chunk.choices[0].delta.content

                if content:
                    yield content

        except Exception as exc:
            raise AIProviderError(
                "Failed to generate streaming response from OpenAI."
            ) from exc