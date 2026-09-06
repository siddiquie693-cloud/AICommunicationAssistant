from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT


class PromptManager:
    """
    Centralized manager for constructing AI prompts.
    """

    SYSTEM_PROMPTS = {
        "conversation": CONVERSATION_SYSTEM_PROMPT,
    }

    @staticmethod
    def get_conversation_system_prompt() -> str:
        """
        Return the system prompt used for conversations.
        """
        return CONVERSATION_SYSTEM_PROMPT

    @classmethod
    def get_system_prompt(cls, prompt_type: str) -> str:
        """
        Return a system prompt based on the prompt type.
        """
        if not prompt_type or not prompt_type.strip():
            raise ValueError("Prompt type cannot be empty.")

        prompt_type = prompt_type.strip().lower()

        try:
            return cls.SYSTEM_PROMPTS[prompt_type]
        except KeyError:
            raise ValueError(
                f"Unknown prompt type: {prompt_type}"
            )

    @classmethod
    def validate_system_prompts(cls) -> None:
        """
        Validate that all registered system prompts are non-empty.
        """
        for prompt_type, prompt in cls.SYSTEM_PROMPTS.items():
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(
                    f"System prompt '{prompt_type}' cannot be empty."
                )

    @staticmethod
    def build_conversation_prompt(
        user_prompt: str,
        *,
        context: str | None = None,
    ) -> str:
        """
        Build a conversation prompt with optional context.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("User prompt cannot be empty.")

        prompt = user_prompt.strip()

        if context and context.strip():
            prompt = (
                f"Conversation context:\n"
                f"{context.strip()}\n\n"
                f"User message:\n"
                f"{prompt}"
            )

        return prompt