from conversations.models import Conversation, Message


class ConversationContextBuilder:
    """
    Builds conversation history for NIRA context.

    Conversation history is limited to the configured message limit
    and returned in chronological order.
    """

    def __init__(self, message_limit: int = 20):
        if message_limit < 0:
            raise ValueError("message_limit cannot be negative.")

        self.message_limit = message_limit

    def build(
        self,
        conversation: Conversation,
        *,
        exclude_message_id: int | None = None,
    ) -> list[dict[str, str]]:
        if not isinstance(conversation, Conversation):
            raise TypeError(
                "conversation must be a Conversation instance."
            )

        messages = conversation.messages.order_by(
            "-created_at",
            "-id",
        )

        if exclude_message_id is not None:
            messages = messages.exclude(
                id=exclude_message_id
            )

        messages = list(
            messages[: self.message_limit]
        )

        messages.reverse()

        return [
            {
                "role": (
                    "user"
                    if message.sender_type == Message.SENDER_USER
                    else "assistant"
                ),
                "content": message.content,
            }
            for message in messages
        ]