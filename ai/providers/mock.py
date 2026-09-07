from ai.providers.base import AIProvider


class MockAIProvider(AIProvider):
    """
    Mock AI provider used for development and testing.

    This provider does not call an external AI service.
    """

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Return a deterministic mock response.
        """

        if not messages or len(messages) == 1:
            return f"Mock AI response: {prompt}"

        formatted_messages = []

        for message in messages:
            role = message["role"].capitalize()
            content = message["content"]

            formatted_messages.append(
                f"{role}: {content}"
            )

        conversation_context = "\n".join(
            formatted_messages
        )    

        return (
            f"Mock AI response: "
            f"{conversation_context}"
        )

    def generate_stream(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ):
        """
        Generate a response as a stream of text chunks.
        """

        response = self.generate(
            prompt,
            system_prompt=system_prompt,
            messages=messages,
        )

        chunk_size = 10

        for index in range(0, len(response), chunk_size):
            yield response[index:index + chunk_size]