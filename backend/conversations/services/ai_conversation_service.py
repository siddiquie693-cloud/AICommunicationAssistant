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

    def _build_prompt(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> str:
        """
        Build a prompt containing the previous conversation history
        and the current user message.
        """

        messages = (
            conversation.messages
            .filter(created_at__lte=user_message.created_at)
            .order_by("created_at", "id")
        )

        history = []

        for message in messages:
            if message.sender_type == Message.SENDER_USER:
                role = "User"
            else:
                role = "Assistant"

            history.append(
                f"{role}: {message.content}"
            )

        return "\n".join(history)

    def generate_response(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> Message:
        """
        Generate an AI response using the conversation history
        and save it to the same conversation.
        """

        prompt = self._build_prompt(
            conversation,
            user_message,
        )

        response_text = self.ai_service.generate_response(
            prompt,
        )

        return Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content=response_text,
        )