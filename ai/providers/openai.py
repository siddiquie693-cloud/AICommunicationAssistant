from decouple import config
from openai import OpenAI

from ai.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    """
    AI provider implementation using OpenAI.
    """

    def __init__(self):
        self.api_key = config("OPENAI_API_KEY", default="")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = config(
            "OPENAI_MODEL",
            default="gpt-4o-mini",
        )

        self.client = OpenAI(
            api_key=self.api_key,
        )

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response using OpenAI.
        """

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content or ""