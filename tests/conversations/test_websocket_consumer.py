from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken
from conversations.models import Conversation, Message

from ai.services.ai_service import AIService

from config.asgi import application
from users.models import User
from django.utils import timezone
from unittest.mock import patch

class ConversationConsumerTests(TransactionTestCase):

    def test_unauthenticated_websocket_connection_is_rejected(self):
        async_to_sync(
            self._test_unauthenticated_connection
        )()

    async def _test_unauthenticated_connection(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/conversations/1/",
        )

        connected, _ = await communicator.connect()

        self.assertFalse(connected)

        await communicator.disconnect()

    def test_authenticated_websocket_connection_and_acknowledgement(
        self,
    ):
        user_id, access_token = self._create_test_user(
            "websocket_user",
            "websocket@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Test Conversation",
        )

        async_to_sync(
            self._test_authenticated_connection
        )(
            access_token,
            user_id,
            conversation.id,
        )

    async def _test_authenticated_connection(
        self,
        access_token,
        user_id,
        conversation_id,
    ):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.send_json_to(
            {
                "message": "Hello",
            }
        )

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "message_recevied",
        )

        self.assertEqual(
            response["conversation_id"],
            conversation_id,
        )

        self.assertEqual(
            response["message"],
            "Hello",
        )

        message_exists = await self._message_exists(
            response["message_id"],
            conversation_id,
        )

        self.assertTrue(message_exists)

        assistant_message_exists = await self._assistant_message_exists(
            response["conversation_id"],
            response["response"],
        )

        self.assertTrue(assistant_message_exists)

        await communicator.disconnect()

    def test_authenticated_websocket_rejects_other_users_conversation(
        self,
    ):
        owner_id, _ = self._create_test_user(
            "conversation_owner",
            "owner@example.com",
        )

        _, attacker_token = self._create_test_user(
            "conversation_attacker",
            "attacker@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=owner_id,
            title="Owner Conversation",
        )

        async_to_sync(
            self._test_rejected_conversation_connection
        )(
            attacker_token,
            conversation.id,
        )

    async def _test_rejected_conversation_connection(
        self,
        access_token,
        conversation_id,
    ):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected, _ = await communicator.connect()

        self.assertFalse(connected)

        await communicator.disconnect()

    def test_authenticated_websocket_rejects_deleted_conversation(
        self,
    ):
        user_id, access_token = self._create_test_user(
            "deleted_conversation_user",
            "deleted@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Deleted Conversation",
        )

        conversation.deleted_at = timezone.now()
        conversation.save(update_fields=["deleted_at"])

        async_to_sync(
            self._test_rejected_conversation_connection
        )(
            access_token,
            conversation.id,
        )    

    def test_authenticated_websocket_rejects_missing_message(self):
        user_id, access_token = self._create_test_user(
            "missing_message_user",
            "missing@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Missing Message Test Conversation",
        )

        async_to_sync(
            self._test_invalid_message
        )(
            access_token,
            conversation.id,
            {},
        )

    def test_authenticated_websocket_rejects_empty_message(self):
        user_id, access_token = self._create_test_user(
            "empty_message_user",
            "empty@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Empty Message Test Conversation",
        )

        async_to_sync(
            self._test_invalid_message
        )(
            access_token,
            conversation.id,
            {
                "message": "   ",
            },
        )

    async def _test_invalid_message(
        self,
        access_token,
        conversation_id,
        payload,
    ):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.send_json_to(payload)

        response = await communicator.receive_json_from()

        self.assertEqual(
            response,
            {
                "type": "error",
                "code": "invalid_message",
                "message": "Message cannot be empty.",
            },
        )

        await communicator.disconnect()

    def _create_test_user(
        self,
        username,
        email,
    ):
        return async_to_sync(
            self._create_test_user_async
        )(
            username,
            email,
        )

    @database_sync_to_async
    def _create_test_user_async(
        self,
        username,
        email,
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password="TestPassword123!",
        )

        access_token = str(
            RefreshToken.for_user(user).access_token
        )

        return user.id, access_token

    @database_sync_to_async
    def _message_exists(
        self,
        message_id,
        conversation_id,
    ):
        return Message.objects.filter(
            id=message_id,
            conversation_id=conversation_id,
            sender_type=Message.SENDER_USER,
            content="Hello",
        ).exists()

    @database_sync_to_async
    def _assistant_message_exists(
        self,
        conversation_id,
        content,
    ):
        return Message.objects.filter(
            conversation_id=conversation_id,
            sender_type=Message.SENDER_ASSISTANT,
            content=content,
        ).exists()

    def test_websocket_returns_error_when_ai_response_fails(self):
        user_id, access_token = self._create_test_user(
            "ai_error_user",
            "aierror@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="AI Error Test Conversation",
        )

        async_to_sync(
            self._test_ai_response_error
        )(
            access_token,
            conversation.id,
        )

    async def _test_ai_response_error(
        self,
        access_token,
        conversation_id,
    ):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        with patch(
            "conversations.consumers.generate_ai_response",
        ) as mock_generate_ai_response:

            mock_generate_ai_response.side_effect = Exception(
                "AI service failed"
            )

            await communicator.send_json_to(
                {
                    "message": "Hello",
                }
            )

            response = await communicator.receive_json_from()

            mock_generate_ai_response.assert_called_once()

        self.assertEqual(
            response,
            {
                "type": "error",
                "code": "ai_response_error",
                "message": "Unable to generate AI response.",
            },
        )

        await communicator.disconnect()