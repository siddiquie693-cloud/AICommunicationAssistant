from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from ai.services.ai_service import AIService
from .services.ai_conversation_service import AIConversationService
from .models import Conversation, Message


@database_sync_to_async
def get_user_conversation(conversation_id, user):
    return Conversation.objects.filter(
        id=conversation_id,
        user=user,
        deleted_at__isnull=True,
    ).first()

@database_sync_to_async
def create_user_message(conversation, content):
    return Message.objects.create(
        conversation=conversation,
        sender_type=Message.SENDER_USER,
        content=content,
    )

@database_sync_to_async
def generate_ai_response(conversation, user_message):
    service = AIConversationService()

    return service.generate_response(
        conversation,
        user_message,
    )


class ConversationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope.get("user")

        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        conversation_id = self.scope["url_route"]["kwargs"].get(
            "conversation_id"
        )

        conversation = await get_user_conversation(
            conversation_id,
            user,
        )

        if conversation is None:
            await self.close(code=4004)
            return

        self.conversation = conversation

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content, **kwargs):
        message = content.get("message")

        if not isinstance(message, str) or not message.strip():
            await self.send_json(
                {
                    "type": "error",
                    "code": "invalid_message",
                    "message": "Message cannot be empty.",
                }
            )
            return

        conversation_id = self.scope["url_route"]["kwargs"].get(
            "conversation_id"
        )

        user_message = await create_user_message(
            self.conversation,
            message.strip(),
        )

        try:
            assistant_message = await generate_ai_response(
                self.conversation,
                user_message,
            )
        except Exception:
            await self.send_json(
                {
                    "type": "error",
                    "code": "ai_response_error",
                    "message": "Unable to generate AI response.",
                }
            )    
            return 

        await self.send_json(
            {
                "type": "message_recevied",
                "message_id": user_message.id,
                "conversation_id": int(conversation_id),
                "message": user_message.content,
                "response": assistant_message.content,
            }
        )