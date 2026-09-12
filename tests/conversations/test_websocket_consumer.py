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

        user_response = await communicator.receive_json_from()

        self.assertEqual(
            user_response["type"],
            "user_message",
        )

        self.assertEqual(
            user_response["conversation_id"],
            conversation_id,
        )

        self.assertEqual(
            user_response["message"],
            "Hello",
        )

        assistant_response = await communicator.receive_json_from()

        self.assertEqual(
            assistant_response["type"],
            "assistant_message",
        )

        self.assertEqual(
            assistant_response["conversation_id"],
            conversation_id,
        )

        message_exists = await self._message_exists(
            user_response["message_id"],
            conversation_id,
        )

        self.assertTrue(message_exists)

        self._assistant_message_exists = await self._assistant_message_exists(
            conversation_id,
            assistant_response["response"],
        )

        self.assertTrue(self._assistant_message_exists)

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

    def test_rejects_non_string_message(self):
        user_id, access_token = self._create_test_user(
            "websocket_type_user",
            "websocket_type@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Type Test",
        )

        async_to_sync(
            self._test_rejects_non_string_message
        )(
            access_token,
            conversation.id,
        )


    async def _test_rejects_non_string_message(
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

            await communicator.send_json_to(
                {
                    "message": 123,
                }
            )

            response = await communicator.receive_json_from()

            self.assertEqual(
                response["type"],
                "error",
            )

            self.assertEqual(
                response["code"],
                "invalid_message",
            )

            self.assertEqual(
                response["message"],
                "Message cannot be empty.",
            )

            await communicator.disconnect()

    def test_rejects_missing_message_field(self):
        user_id, access_token = self._create_test_user(
            "websocket_missing_user",
            "websocket_missing@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Missing Message Test",
        )

        async_to_sync(
            self._test_rejects_missing_message_field
        )(
            access_token,
            conversation.id,
        )


    async def _test_rejects_missing_message_field(
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

        await communicator.send_json_to({})

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "error",
        )

        self.assertEqual(
            response["code"],
            "invalid_message",
        )

        self.assertEqual(
            response["message"],
            "Message cannot be empty.",
        )

        await communicator.disconnect() 

    def test_rejects_whitespace_only_message(self):
        user_id, access_token = self._create_test_user(
            "websocket_whitespace_user",
            "websocket_whitespace@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Whitespace Test",
        )

        async_to_sync(
            self._test_rejects_whitespace_only_message
        )(
            access_token,
            conversation.id,
        )       

    async def _test_rejects_whitespace_only_message(
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

        await communicator.send_json_to(
            {
                "message": "   ",
            }
        )

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "error",
        )

        self.assertEqual(
            response["code"],
            "invalid_message",
        )

        self.assertEqual(
            response["message"],
            "Message cannot be empty.",
        )

        await communicator.disconnect()  

    def test_rejects_message_exceeding_maximum_length(self):
        user_id, access_token = self._create_test_user(
            "websocket_length_user",
            "websocket_length@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Message Length Test",
        )

        async_to_sync(
            self._test_rejects_message_exceeding_maximum_length
        )(
            access_token,
            conversation.id,
        )          

    async def _test_rejects_message_exceeding_maximum_length(
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

        await communicator.send_json_to(
            {
                "message": "a" * 10001,
            }
        )

        response = await communicator.receive_json_from()

        self.assertEqual(
            response["type"],
            "error",
        )

        self.assertEqual(
            response["code"],
            "message_too_long",
        )

        self.assertEqual(
            response["message"],
            "Message exceeds the maximum allowed length.",
        )

        await communicator.disconnect() 

    def test_accepts_message_at_maximum_length(self):
        user_id, access_token = self._create_test_user(
            "websocket_boundary_user",
            "websocket_boundary@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Boundary Test",
        )

        async_to_sync(
            self._test_accepts_message_at_maximum_length
        )(
            access_token,
            conversation.id,
        )

    async def _test_accepts_message_at_maximum_length(
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

        message = "a" * 10000

        await communicator.send_json_to(
            {
                "message": message,
            }
        )

        user_response = await communicator.receive_json_from()

        self.assertEqual(
            user_response["type"],
            "user_message",
        )

        self.assertEqual(
            user_response["conversation_id"],
            conversation_id,
        )

        self.assertEqual(
            user_response["message"],
            message,
        )

        assistant_response = await communicator.receive_json_from()

        self.assertEqual(
            assistant_response["type"],
            "assistant_message",
        )

        self.assertEqual(
            assistant_response["conversation_id"],
            conversation_id,
        )

        await communicator.disconnect() 

    def test_strips_whitespace_from_valid_message(self):
        user_id, access_token = self._create_test_user(
            "websocket_strip_user",
            "websocket_strip@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Whitespace Strip Test",
        )

        async_to_sync(
            self._test_strips_whitespace_from_valid_message
        )(
            access_token,
            conversation.id,
        )


    async def _test_strips_whitespace_from_valid_message(
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

        await communicator.send_json_to(
            {
                "message": "   Hello WebSocket   ",
            }
        )

        user_response = await communicator.receive_json_from()

        self.assertEqual(
            user_response["type"],
            "user_message",
        )

        self.assertEqual(
            user_response["message"],
            "Hello WebSocket",
        )

        self.assertEqual(
            user_response["conversation_id"],
            conversation_id,
        )

        assistant_response = await communicator.receive_json_from()

        self.assertEqual(
            assistant_response["type"],
            "assistant_message",
        )

        self.assertEqual(
            assistant_response["conversation_id"],
            conversation_id,
        )

        await communicator.disconnect() 

    def test_persists_stripped_message_content(self):
        user_id, access_token = self._create_test_user(
            "websocket_persist_user",
            "websocket_persist@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Persistence Test",
        )

        async_to_sync(
            self._test_persists_stripped_message_content
        )(
            access_token,
            conversation.id,
        )

    async def _test_persists_stripped_message_content(
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

        await communicator.send_json_to(
            {
                "message": "   Persisted WebSocket Message   ",
            }
        )

        user_response = await communicator.receive_json_from()

        self.assertEqual(
            user_response["type"],
            "user_message",
        )

        message_exists = await self._message_exists_with_content(
            user_response["message_id"],
            conversation_id,
            "Persisted WebSocket Message",
        )

        self.assertTrue(message_exists)

        await communicator.receive_json_from()

        await communicator.disconnect()

    @database_sync_to_async
    def _message_exists_with_content(
        self,
        message_id,
        conversation_id,
        content,
    ):
        return Message.objects.filter(
            id=message_id,
            conversation_id=conversation_id,
            content=content,
            sender_type=Message.SENDER_USER,
        ).exists()                

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