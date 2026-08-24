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
