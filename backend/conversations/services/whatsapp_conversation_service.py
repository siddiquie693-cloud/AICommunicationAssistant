from conversations.models import Conversation, Message
from conversations.services.ai_conversation_service import (
    AIConversationService,
)
from ai.whatsapp.service import WhatsAppService
from django.contrib.auth import get_user_model

class WhatsAppConversationService:
    """
    Orchestrates WhatsApp messages with the AI conversation service.
    """

    def __init__(
        self,
        whatsapp_service: WhatsAppService,
        ai_conversation_service=None,
    ):
        self.whatsapp_service = whatsapp_service

        if ai_conversation_service is None:
            ai_conversation_service = AIConversationService()

        self.ai_conversation_service = ai_conversation_service

    def get_or_create_conversation(
        self,
        user,
        conversation_id=None,
    ):
        if conversation_id is not None:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=user,
            )
            return conversation

        return Conversation.objects.create(
            user=user,
            title="WhatsApp Conversation",
        )

    def get_user_by_whatsapp_number(
        self,
        phone_number,
    ):
        if not phone_number or not str(phone_number).strip():
            raise ValueError("WhatsApp phone number cannot be empty.")

        User = get_user_model()

        try:
            return User.objects.get(
                whatsapp_phone_number=str(phone_number).strip(),
            )
        except User.DoesNotExist:
            raise ValueError(
                "No user found for the WhatsApp phone number."
            )

    def process_message(
        self,
        user,
        recipient,
        message,
        *,
        conversation_id=None,
        target_language=None,
    ):
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Message cannot be empty.")

        conversation = self.get_or_create_conversation(
            user,
            conversation_id=conversation_id,
        )

        user_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content=message.strip(),
        )

        assistant_message = (
            self.ai_conversation_service.generate_response(
                conversation,
                user_message,
                target_language=target_language,
            )
        )

        self.whatsapp_service.send_message(
            recipient,
            assistant_message.content,
        )

        return {
            "conversation": conversation,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }