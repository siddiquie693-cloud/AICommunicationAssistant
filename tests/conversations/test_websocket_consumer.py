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
from unittest.mock import patch, AsyncMock

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

    def test_websocket_disconnect_removes_client_from_conversation_group(
        self,
    ):
        user_id, access_token = self._create_test_user(
            "websocket_disconnect_user",
            "websocket_disconnect@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="WebSocket Disconnect Test",
        )

        async_to_sync(
            self._test_websocket_disconnect_removes_client_from_conversation_group
        )(
            access_token,
            conversation.id,
        )

    async def _test_websocket_disconnect_removes_client_from_conversation_group(
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
            "channels.layers.InMemoryChannelLayer.group_discard",
            new_callable=AsyncMock,
        ) as mock_group_discard:

            await communicator.disconnect()

            mock_group_discard.assert_awaited_once()

            self.assertEqual(
                mock_group_discard.call_args.args[0],
                f"conversation_{conversation_id}",
            )    

    def test_multiple_clients_receive_same_conversation_events(self):
        user_id, access_token = self._create_test_user(
            "multi_client_user",
            "multiclient@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Multiple Client Conversation",
        )

        async_to_sync(
            self._test_multiple_clients_receive_same_conversation_events
        )(
            access_token,
            conversation.id,
        )

    async def _test_multiple_clients_receive_same_conversation_events(
        self,
        access_token,
        conversation_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        with patch(
            "conversations.consumers.generate_ai_response",
            new_callable=AsyncMock,
        ) as mock_generate_ai_response:

            mock_generate_ai_response.return_value = (
                await database_sync_to_async(Message.objects.create)(
                    conversation_id=conversation_id,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="AI response",
                )
            )

            await communicator_one.send_json_to(
                {
                    "message": "Hello",
                }
            )

            user_event_one = await communicator_one.receive_json_from()
            user_event_two = await communicator_two.receive_json_from()

            self.assertEqual(
                user_event_one["type"],
                "user_message",
            )

            self.assertEqual(
                user_event_two["type"],
                "user_message",
            )

            self.assertEqual(
                user_event_one["message"],
                user_event_two["message"],
            )

            self.assertEqual(
                user_event_one["message_id"],
                user_event_two["message_id"],
            )

            assistant_event_one = await communicator_one.receive_json_from()
            assistant_event_two = await communicator_two.receive_json_from()

            self.assertEqual(
                assistant_event_one["type"],
                "assistant_message",
            )

            self.assertEqual(
                assistant_event_two["type"],
                "assistant_message",
            )

            self.assertEqual(
                assistant_event_one["response"],
                assistant_event_two["response"],
            )

        await communicator_one.disconnect()
        await communicator_two.disconnect()   

    def test_clients_receive_only_their_conversation_events(self):
        user_id, access_token = self._create_test_user(
            "conversation_isolation_user",
            "isolation@example.com",
        )

        conversation_one = Conversation.objects.create(
            user_id=user_id,
            title="Conversation One",
        )

        conversation_two = Conversation.objects.create(
            user_id=user_id,
            title="Conversation Two",
        )

        async_to_sync(
            self._test_clients_receive_only_their_conversation_events
        )(
            access_token,
            conversation_one.id,
            conversation_two.id,
        )


    async def _test_clients_receive_only_their_conversation_events(
        self,
        access_token,
        conversation_one_id,
        conversation_two_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_one_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_two_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        with patch(
            "conversations.consumers.generate_ai_response",
            new_callable=AsyncMock,
        ) as mock_generate_ai_response:

            mock_generate_ai_response.return_value = (
                await database_sync_to_async(Message.objects.create)(
                    conversation_id=conversation_one_id,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="Conversation one response",
                )
            )

            await communicator_one.send_json_to(
                {
                    "message": "Message for conversation one",
                }
            )

            event_one = await communicator_one.receive_json_from()

            self.assertEqual(
                event_one["type"],
                "user_message",
            )

            self.assertEqual(
                event_one["conversation_id"],
                conversation_one_id,
            )

            assistant_event_one = await communicator_one.receive_json_from()

            self.assertEqual(
                assistant_event_one["type"],
                "assistant_message",
            )

            self.assertEqual(
                assistant_event_one["conversation_id"],
                conversation_one_id,
            )

            has_event_for_conversation_two = await communicator_two.receive_nothing(
                timeout=0.5,
            )

            self.assertTrue(has_event_for_conversation_two)

        await communicator_one.disconnect()
        await communicator_two.disconnect()         

    def test_disconnected_client_does_not_receive_conversation_events(self):
        user_id, access_token = self._create_test_user(
            "disconnected_client_user",
            "disconnected@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Disconnected Client Conversation",
        )

        async_to_sync(
            self._test_disconnected_client_does_not_receive_conversation_events
        )(
            access_token,
            conversation.id,
        )

    async def _test_disconnected_client_does_not_receive_conversation_events(
        self,
        access_token,
        conversation_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        await communicator_two.disconnect()

        with patch(
            "conversations.consumers.generate_ai_response",
            new_callable=AsyncMock,
        ) as mock_generate_ai_response:

            mock_generate_ai_response.return_value = (
                await database_sync_to_async(Message.objects.create)(
                    conversation_id=conversation_id,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="AI response",
                )
            )

            await communicator_one.send_json_to(
                {
                    "message": "Hello",
                }
            )

            event_one = await communicator_one.receive_json_from()

            self.assertEqual(
                event_one["type"],
                "user_message",
            )

            self.assertEqual(
                event_one["conversation_id"],
                conversation_id,
            )

            assistant_event_one = await communicator_one.receive_json_from()

            self.assertEqual(
                assistant_event_one["type"],
                "assistant_message",
            )

            self.assertEqual(
                assistant_event_one["conversation_id"],
                conversation_id,
            )

            has_event_for_disconnected_client = (
                await communicator_two.receive_nothing(
                    timeout=0.5,
                )
            )

            self.assertTrue(
                has_event_for_disconnected_client,
            )

        await communicator_one.disconnect()   

    def test_ai_response_error_is_not_broadcast_to_other_clients(self):
        user_id, access_token = self._create_test_user(
            "ai_error_multi_client_user",
            "aierrormulti@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="AI Error Multi Client Conversation",
        )

        async_to_sync(
            self._test_ai_response_error_is_not_broadcast_to_other_clients
        )(
            access_token,
            conversation.id,
        )

    async def _test_ai_response_error_is_not_broadcast_to_other_clients(
        self,
        access_token,
        conversation_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        with patch(
            "conversations.consumers.generate_ai_response",
        ) as mock_generate_ai_response:

            mock_generate_ai_response.side_effect = Exception(
                "AI service failed"
            )

            await communicator_one.send_json_to(
                {
                    "message": "Hello",
                }
            )

            event_one = await communicator_one.receive_json_from()
            event_two = await communicator_one.receive_json_from()

            events_one = [
                event_one,
                event_two,
            ]

            event_types_one = {
                event["type"]
                for event in events_one
            }

            self.assertEqual(
                event_types_one,
                {
                    "user_message",
                    "error",
                },
            )

            error_events = [
                event
                for event in events_one
                if event["type"] == "error"
            ]

            self.assertEqual(
                error_events,
                [
                    {
                        "type": "error",
                        "code": "ai_response_error",
                        "message": "Unable to generate AI response.",
                    }
                ],
            )

            user_events_one = [
                event
                for event in events_one
                if event["type"] == "user_message"
            ]

            self.assertEqual(
                len(user_events_one),
                1,
            )

            user_event_two = await communicator_two.receive_json_from()

            self.assertEqual(
                user_event_two["type"],
                "user_message",
            )

            no_additional_event = await communicator_two.receive_nothing(
                timeout=0.5,
            )

            self.assertTrue(no_additional_event)

            mock_generate_ai_response.assert_called_once()

        await communicator_one.disconnect()
        await communicator_two.disconnect()

    def test_multiple_clients_receive_same_ai_response(self):
        user_id, access_token = self._create_test_user(
            "ai_success_multi_client_user",
            "aisuccessmulti@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="AI Success Multi Client Conversation",
        )

        async_to_sync(
            self._test_multiple_clients_receive_same_ai_response
        )(
            access_token,
            conversation.id,
        )

    async def _test_multiple_clients_receive_same_ai_response(
        self,
        access_token,
        conversation_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        with patch(
            "conversations.consumers.generate_ai_response",
        ) as mock_generate_ai_response:

            mock_generate_ai_response.return_value = (
                await database_sync_to_async(Message.objects.create)(
                    conversation_id=conversation_id,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="Hello! How can I help you?",
                )
            )

            await communicator_one.send_json_to(
                {
                    "message": "Hello",
                }
            )

            events_one = [
                await communicator_one.receive_json_from(),
                await communicator_one.receive_json_from(),
            ]

            events_two = [
                await communicator_two.receive_json_from(),
                await communicator_two.receive_json_from(),
            ]

            assistant_event_one = next(
                event
                for event in events_one
                if event["type"] == "assistant_message"
            )

            assistant_event_two = next(
                event
                for event in events_two
                if event["type"] == "assistant_message"
            )

            self.assertEqual(
                assistant_event_one,
                assistant_event_two,
            )

            self.assertEqual(
                assistant_event_one["response"],
                "Hello! How can I help you?",
            )

            mock_generate_ai_response.assert_called_once()

        await communicator_one.disconnect()
        await communicator_two.disconnect()  

    def test_ai_response_is_persisted_in_conversation(self):
        user_id, access_token = self._create_test_user(
            "ai_persist_user",
            "aipersist@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="AI Persist Conversation",
        )

        async_to_sync(
            self._test_ai_response_is_persisted_in_conversation
        )(
            access_token,
            conversation.id,
        )

    async def _test_ai_response_is_persisted_in_conversation(
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

            mock_generate_ai_response.return_value = (
                await database_sync_to_async(Message.objects.create)(
                    conversation_id=conversation_id,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="This response should be persisted.",
                )
            )

            await communicator.send_json_to(
                {
                    "message": "Hello",
                }
            )

            response_one = await communicator.receive_json_from()
            response_two = await communicator.receive_json_from()

            events = [
                response_one,
                response_two,
            ]

            assistant_event = next(
                event
                for event in events
                if event["type"] == "assistant_message"
            )

            self.assertEqual(
                assistant_event["response"],
                "This response should be persisted.",
            )

            mock_generate_ai_response.assert_called_once()

        assistant_message = await database_sync_to_async(
            Message.objects.filter(
                conversation_id=conversation_id,
                sender_type=Message.SENDER_ASSISTANT,
            ).first
        )()

        self.assertIsNotNone(assistant_message)

        self.assertEqual(
            assistant_message.content,
            "This response should be persisted.",
        )

        await communicator.disconnect() 

    def test_user_and_ai_messages_are_persisted_in_order(self):
        user_id, access_token = self._create_test_user(
            "message_order_user",
            "messageorder@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Message Order Conversation",
        )

        async_to_sync(
            self._test_user_and_ai_messages_are_persisted_in_order
        )(
            access_token,
            conversation.id,
        )

    async def _test_user_and_ai_messages_are_persisted_in_order(
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

            async def create_assistant_message(
                conversation,
                user_message,
            ):
                return await database_sync_to_async(
                    Message.objects.create
                )(
                    conversation=conversation,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="Assistant response",
                )

            mock_generate_ai_response.side_effect = (
                create_assistant_message
            )

            await communicator.send_json_to(
                {
                    "message": "User message",
                }
            )

            first_event = await communicator.receive_json_from()
            second_event = await communicator.receive_json_from()

            events = [
                first_event,
                second_event,
            ]

            event_types = [
                event["type"]
                for event in events
            ]

            self.assertIn(
                "user_message",
                event_types,
            )

            self.assertIn(
                "assistant_message",
                event_types,
            )

            mock_generate_ai_response.assert_called_once()

        messages = await database_sync_to_async(
            lambda: list(
                Message.objects.filter(
                    conversation_id=conversation_id,
                ).order_by("id")
            )
        )()

        self.assertEqual(
            len(messages),
            2,
        )

        self.assertEqual(
            messages[0].sender_type,
            Message.SENDER_USER,
        )

        self.assertEqual(
            messages[0].content,
            "User message",
        )

        self.assertEqual(
            messages[1].sender_type,
            Message.SENDER_ASSISTANT,
        )

        self.assertEqual(
            messages[1].content,
            "Assistant response",
        )

        await communicator.disconnect()

    def test_multiple_messages_are_processed_in_same_websocket_connection(self):
        user_id, access_token = self._create_test_user(
            "multiple_messages_user",
            "multiplemessages@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="Multiple Messages Conversation",
        )

        async_to_sync(
            self._test_multiple_messages_are_processed_in_same_websocket_connection
        )(
            access_token,
            conversation.id,
        )


    async def _test_multiple_messages_are_processed_in_same_websocket_connection(
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

        assistant_responses = [
            "First assistant response",
            "Second assistant response",
        ]

        response_index = 0

        async def create_assistant_message(
            conversation,
            user_message,
        ):
            nonlocal response_index

            response = assistant_responses[response_index]
            response_index += 1

            return await database_sync_to_async(
                Message.objects.create
            )(
                conversation=conversation,
                sender_type=Message.SENDER_ASSISTANT,
                content=response,
            )

        with patch(
            "conversations.consumers.generate_ai_response",
            side_effect=create_assistant_message,
        ) as mock_generate_ai_response:

            await communicator.send_json_to(
                {
                    "message": "First user message",
                }
            )

            first_event_one = await communicator.receive_json_from()
            first_event_two = await communicator.receive_json_from()

            first_events = [
                first_event_one,
                first_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in first_events
                },
                {
                    "user_message",
                    "assistant_message",
                },
            )

            await communicator.send_json_to(
                {
                    "message": "Second user message",
                }
            )

            second_event_one = await communicator.receive_json_from()
            second_event_two = await communicator.receive_json_from()

            second_events = [
                second_event_one,
                second_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in second_events
                },
                {
                    "user_message",
                    "assistant_message",
                },
            )

            mock_generate_ai_response.assert_called()
            self.assertEqual(
                mock_generate_ai_response.call_count,
                2,
            )

        messages = await database_sync_to_async(
            lambda: list(
                Message.objects.filter(
                    conversation_id=conversation_id,
                ).order_by("id")
            )
        )()

        self.assertEqual(
            len(messages),
            4,
        )

        self.assertEqual(
            [
                message.content
                for message in messages
            ],
            [
                "First user message",
                "First assistant response",
                "Second user message",
                "Second assistant response",
            ],
        )

        await communicator.disconnect()

    def test_ai_responses_are_isolated_between_conversations(self):
        user_id, access_token = self._create_test_user(
            "ai_isolation_user",
            "aiisolation@example.com",
        )

        conversation_one = Conversation.objects.create(
            user_id=user_id,
            title="AI Isolation Conversation One",
        )

        conversation_two = Conversation.objects.create(
            user_id=user_id,
            title="AI Isolation Conversation Two",
        )

        async_to_sync(
            self._test_ai_responses_are_isolated_between_conversations
        )(
            access_token,
            conversation_one.id,
            conversation_two.id,
        )


    async def _test_ai_responses_are_isolated_between_conversations(
        self,
        access_token,
        conversation_one_id,
        conversation_two_id,
    ):
        communicator_one = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_one_id}/?token={access_token}",
        )

        communicator_two = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_two_id}/?token={access_token}",
        )

        connected_one, _ = await communicator_one.connect()
        connected_two, _ = await communicator_two.connect()

        self.assertTrue(connected_one)
        self.assertTrue(connected_two)

        async def create_assistant_message(
            conversation,
            user_message,
        ):
            return await database_sync_to_async(
                Message.objects.create
            )(
                conversation=conversation,
                sender_type=Message.SENDER_ASSISTANT,
                content=f"Response for conversation {conversation.id}",
            )

        with patch(
            "conversations.consumers.generate_ai_response",
            side_effect=create_assistant_message,
        ) as mock_generate_ai_response:

            await communicator_one.send_json_to(
                {
                    "message": "Message for conversation one",
                }
            )

            conversation_one_event_one = (
                await communicator_one.receive_json_from()
            )

            conversation_one_event_two = (
                await communicator_one.receive_json_from()
            )

            conversation_one_events = [
                conversation_one_event_one,
                conversation_one_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in conversation_one_events
                },
                {
                    "user_message",
                    "assistant_message",
                },
            )

            assistant_event_one = next(
                event
                for event in conversation_one_events
                if event["type"] == "assistant_message"
            )

            self.assertEqual(
                assistant_event_one["conversation_id"],
                conversation_one_id,
            )

            self.assertEqual(
                assistant_event_one["response"],
                f"Response for conversation {conversation_one_id}",
            )

            no_event_for_conversation_two = (
                await communicator_two.receive_nothing(
                    timeout=0.5,
                )
            )

            self.assertTrue(
                no_event_for_conversation_two
            )

            await communicator_two.send_json_to(
                {
                    "message": "Message for conversation two",
                }
            )

            conversation_two_event_one = (
                await communicator_two.receive_json_from()
            )

            conversation_two_event_two = (
                await communicator_two.receive_json_from()
            )

            conversation_two_events = [
                conversation_two_event_one,
                conversation_two_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in conversation_two_events
                },
                {
                    "user_message",
                    "assistant_message",
                },
            )

            assistant_event_two = next(
                event
                for event in conversation_two_events
                if event["type"] == "assistant_message"
            )

            self.assertEqual(
                assistant_event_two["conversation_id"],
                conversation_two_id,
            )

            self.assertEqual(
                assistant_event_two["response"],
                f"Response for conversation {conversation_two_id}",
            )

            mock_generate_ai_response.assert_called()
            self.assertEqual(
                mock_generate_ai_response.call_count,
                2,
            )

        await communicator_one.disconnect()
        await communicator_two.disconnect()   

    def test_ai_failure_does_not_disconnect_websocket_connection(self):
        user_id, access_token = self._create_test_user(
            "ai_recovery_user",
            "airecovery@example.com",
        )

        conversation = Conversation.objects.create(
            user_id=user_id,
            title="AI Recovery Conversation",
        )

        async_to_sync(
            self._test_ai_failure_does_not_disconnect_websocket_connection
        )(
            access_token,
            conversation.id,
        )


    async def _test_ai_failure_does_not_disconnect_websocket_connection(
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

        response_index = 0

        async def generate_response(
            conversation,
            user_message,
        ):
            nonlocal response_index

            response_index += 1

            if response_index == 1:
                return await database_sync_to_async(
                    Message.objects.create
                )(
                    conversation=conversation,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="First successful response",
                )

            raise Exception("AI service failed")

        with patch(
            "conversations.consumers.generate_ai_response",
            side_effect=generate_response,
        ) as mock_generate_ai_response:

            await communicator.send_json_to(
                {
                    "message": "First message",
                }
            )

            first_event_one = await communicator.receive_json_from()
            first_event_two = await communicator.receive_json_from()

            first_events = [
                first_event_one,
                first_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in first_events
                },
                {
                    "user_message",
                    "assistant_message",
                },
            )

            await communicator.send_json_to(
                {
                    "message": "Second message",
                }
            )

            second_event_one = await communicator.receive_json_from()
            second_event_two = await communicator.receive_json_from()

            second_events = [
                second_event_one,
                second_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in second_events
                },
                {
                    "user_message",
                    "error",
                },
            )

            error_event = next(
                event
                for event in second_events
                if event["type"] == "error"
            )

            self.assertEqual(
                error_event,
                {
                    "type": "error",
                    "code": "ai_response_error",
                    "message": "Unable to generate AI response.",
                },
            )

            mock_generate_ai_response.assert_called()
            self.assertEqual(
                mock_generate_ai_response.call_count,
                2,
            )

            await communicator.send_json_to(
                {
                    "message": "Third message",
                }
            )

            third_event_one = await communicator.receive_json_from()
            third_event_two = await communicator.receive_json_from()

            third_events = [
                third_event_one,
                third_event_two,
            ]

            self.assertEqual(
                {
                    event["type"]
                    for event in third_events
                },
                {
                    "user_message",
                    "error",
                },
            )

            self.assertTrue(
                communicator.scope["user"].is_authenticated
            )

        await communicator.disconnect()         