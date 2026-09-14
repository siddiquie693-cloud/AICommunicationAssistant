from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from ai.whatsapp.exceptions import (
    WhatsAppProviderError,
    WhatsAppWebhookError,
)
from ai.whatsapp.meta import MetaWhatsAppProvider


class MetaWhatsAppProviderTests(SimpleTestCase):

    def create_provider(self):
        return MetaWhatsAppProvider(
            access_token="test-access-token",
            phone_number_id="123456789",
            api_version="v23.0",
        )

    def test_provider_initializes_with_explicit_configuration(self):
        provider = self.create_provider()

        self.assertEqual(
            provider.access_token,
            "test-access-token",
        )
        self.assertEqual(
            provider.phone_number_id,
            "123456789",
        )
        self.assertEqual(
            provider.api_version,
            "v23.0",
        )

    def test_messages_url_is_built_correctly(self):
        provider = self.create_provider()

        self.assertEqual(
            provider.messages_url,
            "https://graph.facebook.com/v23.0/123456789/messages",
        )

    @patch("ai.whatsapp.meta.httpx2.post")
    def test_send_message_sends_correct_payload(
        self,
        mock_post,
    ):
        provider = self.create_provider()

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "messaging_product": "whatsapp",
            "messages": [
                {
                    "id": "wamid.test123",
                }
            ],
        }
        mock_post.return_value = response

        result = provider.send_message(
            "919876543210",
            "Hello from AI assistant",
        )

        self.assertEqual(
            result,
            {
                "messaging_product": "whatsapp",
                "messages": [
                    {
                        "id": "wamid.test123",
                    }
                ],
            },
        )

        mock_post.assert_called_once_with(
            "https://graph.facebook.com/v23.0/123456789/messages",
            headers={
                "Authorization": "Bearer test-access-token",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": "919876543210",
                "type": "text",
                "text": {
                    "body": "Hello from AI assistant",
                },
            },
            timeout=30,
        )

    @patch("ai.whatsapp.meta.httpx2.post")
    def test_send_message_strips_recipient_and_message(
        self,
        mock_post,
    ):
        provider = self.create_provider()

        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "messages": [
                {
                    "id": "wamid.test123",
                }
            ],
        }
        mock_post.return_value = response

        provider.send_message(
            "  919876543210  ",
            "  Hello from AI assistant  ",
        )

        request_kwargs = mock_post.call_args.kwargs

        self.assertEqual(
            request_kwargs["json"]["to"],
            "919876543210",
        )
        self.assertEqual(
            request_kwargs["json"]["text"]["body"],
            "Hello from AI assistant",
        )

    def test_send_message_rejects_empty_recipient(self):
        provider = self.create_provider()

        with self.assertRaises(ValueError) as context:
            provider.send_message(
                "   ",
                "Hello",
            )

        self.assertEqual(
            str(context.exception),
            "Recipient cannot be empty.",
        )

    def test_send_message_rejects_empty_message(self):
        provider = self.create_provider()

        with self.assertRaises(ValueError) as context:
            provider.send_message(
                "919876543210",
                "   ",
            )

        self.assertEqual(
            str(context.exception),
            "Message cannot be empty.",
        )

    @patch("ai.whatsapp.meta.httpx2.post")
    def test_send_message_raises_provider_error_on_http_failure(
        self,
        mock_post,
    ):
        provider = self.create_provider()

        response = Mock()
        response.status_code = 400
        mock_post.return_value = response

        with self.assertRaises(WhatsAppProviderError) as context:
            provider.send_message(
                "919876543210",
                "Hello",
            )

        self.assertIn(
            "WhatsApp Cloud API returned an error (status=400):",
            str(context.exception),
        )

    @patch("ai.whatsapp.meta.httpx2.post")
    def test_send_message_raises_provider_error_on_connection_failure(
        self,
        mock_post,
    ):
        provider = self.create_provider()

        mock_post.side_effect = Exception("Connection failed")

        with self.assertRaises(WhatsAppProviderError) as context:
            provider.send_message(
                "919876543210",
                "Hello",
            )

        self.assertEqual(
            str(context.exception),
            "Unable to connect to WhatsApp Cloud API.",
        )

    @override_settings(WHATSAPP_VERIFY_TOKEN="test-verify-token")
    def test_verify_webhook_returns_challenge(self):
        provider = self.create_provider()

        result = provider.verify_webhook(
            "subscribe",
            "test-verify-token",
            "test-challenge",
        )

        self.assertEqual(
            result,
            "test-challenge",
        )

    @override_settings(WHATSAPP_VERIFY_TOKEN="test-verify-token")
    def test_verify_webhook_rejects_invalid_mode(self):
        provider = self.create_provider()

        with self.assertRaises(WhatsAppWebhookError) as context:
            provider.verify_webhook(
                "invalid",
                "test-verify-token",
                "test-challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Invalid webhook verification mode.",
        )

    @override_settings(WHATSAPP_VERIFY_TOKEN="test-verify-token")
    def test_verify_webhook_rejects_invalid_token(self):
        provider = self.create_provider()

        with self.assertRaises(WhatsAppWebhookError) as context:
            provider.verify_webhook(
                "subscribe",
                "wrong-token",
                "test-challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Invalid webhook verification token.",
        )

    def test_parse_webhook_message_returns_normalized_message(self):
        provider = self.create_provider()

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.test123",
                                        "type": "text",
                                        "text": {
                                            "body": "Hello",
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
        }

        result = provider.parse_webhook_message(payload)

        self.assertEqual(
            result,
            {
                "sender": "919876543210",
                "message": "Hello",
                "message_id": "wamid.test123",
            },
        )

    def test_parse_webhook_message_ignores_status_payload(self):
        provider = self.create_provider()

        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": "wamid.test123",
                                        "status": "delivered",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ],
        }

        result = provider.parse_webhook_message(payload)

        self.assertEqual(result, {})

    def test_provider_requires_access_token(self):
        with self.assertRaises(ValueError) as context:
            MetaWhatsAppProvider(
                access_token="",
                phone_number_id="123456789",
                api_version="v23.0",
            )

        self.assertEqual(
            str(context.exception),
            "WhatsApp access token is not configured.",
        )

    def test_provider_requires_phone_number_id(self):
        with self.assertRaises(ValueError) as context:
            MetaWhatsAppProvider(
                access_token="test-access-token",
                phone_number_id="",
                api_version="v23.0",
            )

        self.assertEqual(
            str(context.exception),
            "WhatsApp phone number ID is not configured.",
        )

    def test_provider_requires_api_version(self):
        with self.assertRaises(ValueError) as context:
            MetaWhatsAppProvider(
                access_token="test-access-token",
                phone_number_id="123456789",
                api_version="",
            )

        self.assertEqual(
            str(context.exception),
            "WhatsApp API version is not configured.",
        )