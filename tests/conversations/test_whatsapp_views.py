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
        "conversations.whatsapp_views.get_whatsapp_provider"
    )
    def test_post_webhook_parses_payload_and_returns_success(self, mock_factory):
        provider = Mock()
        provider.parse_webhook_message.return_value = {
            "message": "Hello",
        }
        mock_factory.return_value = provider

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
            payload,
        )
        provider.parse_webhook_message.assert_called_once_with(
            payload,
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