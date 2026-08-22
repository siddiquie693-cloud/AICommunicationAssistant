from decouple import config
from ai.providers.factory import get_ai_provider
from ai.services.ai_service import AIService

from conversations.models import Conversation, Message


class AIConversationService:
    """
    Application service responsible for generating AI responses
    within a conversation.
    """

    def __init__(self, provider_name=None):
        if provider_name is None:
            provider_name = config(
                "AI_PROVIDER",
                default="mock",
            )
        provider = get_ai_provider(provider_name)
        self.ai_service = AIService(provider)

    def generate_response(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> Message:
        """
        Generate an AI response for a user message and save it
        to the same conversation.
        """

        response_text = self.ai_service.generate_response(
            user_message.content,
        )

        return Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content=response_text,
        )