from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from ai.whatsapp.exceptions import WhatsAppProviderError

class WhatsAppWebhookAPIViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/whatsapp/webhook/"

    @override_settings(
        WHATSAPP_VERIFY_TOKEN="test_whatsapp_token"
    )
    def test_get_webhook_verification_returns_challenge(self):
        response = self.client.get(
            self.url,
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "test_whatsapp_token",
                "hub.challenge": "challenge_123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "challenge_123")

    @override_settings(
        WHATSAPP_VERIFY_TOKEN="test_whatsapp_token"
    )
    def test_get_webhook_verification_rejects_invalid_token(self):
        response = self.client.get(
            self.url,
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_123",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_webhook_verification_failed",
        )

    @override_settings(
        WHATSAPP_VERIFY_TOKEN="test_whatsapp_token"
    )
    def test_get_webhook_verification_rejects_missing_challenge(self):
        response = self.client.get(
            self.url,
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "test_whatsapp_token",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_webhook_verification_failed",
        )

    @patch(
        "conversations.whatsapp_views.WhatsAppConversationService"    
    )
    @patch(
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_parses_payload_and_returns_success(
        self, 
        mock_factory,
        mock_conversation_service,
    ):
        provider = Mock()

        parsed_payload = {
            "sender": "919876543210",
            "message": "Hello",
            "message_id": "wamid.test123",
        }

        provider.parse_webhook_message.return_value = parsed_payload
        mock_factory.return_value = provider

        conversation_service = Mock()
        mock_conversation_service.return_value = conversation_service

        conversation_service.get_user_by_whatsapp_number.return_value = (
            "test-user"
        )

        conversation = Mock()
        conversation.id = 1

        user_message = Mock()
        user_message.id = 2

        assistant_message = Mock()
        assistant_message.id = 3

        conversation_service.process_message.return_value = {
            "conversation": conversation,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

        payload = {
            "message": "Hello",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], True)
        self.assertEqual(
            response.data["payload"],
            {
                "message_id": "wamid.test123",
                "conversation_id": 1,
                "user_message_id": 2,
                "assistant_message_id": 3,
            },
        )
        provider.parse_webhook_message.assert_called_once_with(
            payload,
        )

        conversation_service.get_user_by_whatsapp_number.assert_called_once_with(
            "919876543210",
        )

        conversation_service.process_message.assert_called_once_with(
            "test-user",
            "919876543210",
            "Hello",
        )

    @patch(
    "conversations.whatsapp_views.WhatsAppConversationService"
    )
    @patch(
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_processes_incoming_message(
        self,
        mock_factory,
        mock_conversation_service,
    ):
        provider = Mock()

        parsed_payload = {
            "sender": "919876543210",
            "message": "Hello",
            "message_id": "wamid.test123",
        }

        provider.parse_webhook_message.return_value = parsed_payload
        mock_factory.return_value = provider

        conversation_service = Mock()
        mock_conversation_service.return_value = conversation_service

        conversation_service.get_user_by_whatsapp_number.return_value = (
            "test-user"
        )
        conversation = Mock()
        conversation.id = 1

        user_message = Mock()
        user_message.id = 2

        assistant_message = Mock()
        assistant_message.id = 3

        conversation_service.process_message.return_value = {
            "conversation": conversation,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

        payload = {
            "object": "whatsapp_business_account",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["success"],
            True,
        )

        self.assertEqual(
            response.data["payload"],
            {
                "message_id": "wamid.test123",
                "conversation_id": 1,
                "user_message_id": 2,
                "assistant_message_id": 3,
            },
        )

        conversation_service.get_user_by_whatsapp_number.assert_called_once_with(
            "919876543210",
        )

        conversation_service.process_message.assert_called_once_with(
            "test-user",
            "919876543210",
            "Hello",
        )  

    @patch(
    "conversations.whatsapp_views.WhatsAppConversationService"
    )
    @patch(
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_rejects_unregistered_whatsapp_number(
        self,
        mock_factory,
        mock_conversation_service,
    ):
        provider = Mock()

        provider.parse_webhook_message.return_value = {
            "sender": "919999999999",
            "message": "Hello",
            "message_id": "wamid.unknown123",
        }

        mock_factory.return_value = provider

        conversation_service = Mock()
        mock_conversation_service.return_value = conversation_service

        conversation_service.get_user_by_whatsapp_number.side_effect = (
            ValueError(
                "No user found for the WhatsApp phone number."
            )
        )

        response = self.client.post(
            self.url,
            {
                "object": "whatsapp_business_account",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_webhook_error",
        )
        self.assertEqual(
            response.data["error"]["message"],
            "No user found for the WhatsApp phone number.",
        )      

    @patch(
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_rejects_non_dictionary_payload(
        self,
        mock_factory,
    ):
        provider = Mock()
        provider.parse_webhook_message.side_effect = ValueError(
            "Webhook payload must be a dictionary."
        )
        mock_factory.return_value = provider

        payload = {
            "message": "Hello",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_webhook_error",
        )
        self.assertEqual(
            response.data["error"]["message"],
            "Webhook payload must be a dictionary.",
        )

    @patch(
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_handles_provider_error(
        self,
        mock_factory,
    ):
        provider = Mock()
        provider.parse_webhook_message.side_effect = (
            WhatsAppProviderError("Provider unavailable.")
        )
        mock_factory.return_value = provider

        response = self.client.post(
            self.url,
            {"message": "Hello"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_provider_error",
        )
        self.assertEqual(
            response.data["error"]["message"],
            "WhatsApp provider is currently unavailable.",
        )    

    @override_settings(
        WHATSAPP_VERIFY_TOKEN="test_whatsapp_token"
    )
    def test_get_webhook_verification_rejects_missing_mode(self):
        response = self.client.get(
            self.url,
            {
                "hub.verify_token": "test_whatsapp_token",
                "hub.challenge": "challenge_123",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "whatsapp_webhook_verification_failed",
        )    