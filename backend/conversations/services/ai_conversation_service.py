from ai.providers.factory import get_ai_provider
from ai.services.ai_service import AIService

from conversations.models import Conversation, Message


class AIConversationService:
    """
    Application service responsible for generating AI responses
    within a conversation.
    """

    def __init__(self, provider_name=None):
        provider = get_ai_provider(provider_name)
        self.ai_service = AIService(provider)

    def _build_messages(
        self,
        conversation: Conversation,
    ) -> list[dict[str, str]]:
        """
        Build structured AI messages from conversation history.
        """

        messages = []

        conversation_messages = conversation.messages.order_by(
            "created_at",
            "id",
        )

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

        messages = self._build_messages(conversation)

        response_text = self.ai_service.generate_response(
            user_message.content,
            messages=messages,
        )

        return Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content=response_text,
        )