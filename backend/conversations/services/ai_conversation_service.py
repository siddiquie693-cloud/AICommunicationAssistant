from ai.providers.factory import get_ai_provider
from ai.services.ai_service import AIService
from decouple import config

from conversations.models import Conversation, Message


class AIConversationService:
    """
    Application service responsible for generating AI responses
    within a conversation.
    """

    def __init__(self, provider_name=None):
        provider = get_ai_provider(provider_name)
        self.ai_service = AIService(provider)

        self.memory_message_limit = config(
            "AI_MEMORY_MESSAGE_LIMIT",
            default=20,
            cast=int,
        )

    def _build_messages(
        self,
        conversation: Conversation,
        *,
        exclude_message_id: int | None = None,
    ) -> list[dict[str, str]]:
        """
        Build structured AI messages from conversation history.
        """

        conversation_messages = conversation.messages.order_by(
            "-created_at",
            "-id",
        )

        if exclude_message_id is not None:
            conversation_messages = conversation_messages.exclude(
                id=exclude_message_id,
            )

        conversation_messages = list(
            conversation_messages[: self.memory_message_limit]
        )    

        conversation_messages.reverse()

        messages = []

        for message in conversation_messages:
            role = (
                "user"
                if message.sender_type == Message.SENDER_USER
                else "assistant"
            )

            messages.append(
                {
                    "role": role,
                    "content": message.content,
                }
            )

        return messages    

    def generate_response(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> Message:
        """
        Generate an AI response using the conversation history.
        """

        messages = self._build_messages(
            conversation,
            exclude_message_id=user_message.id,
        )

        response_text = self.ai_service.generate_response(
            user_message.content,
            messages=messages,
        )

        return Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content=response_text,
        )