from django.test import SimpleTestCase
from unittest.mock import patch
from ai.whatsapp.base import WhatsAppProvider
from ai.whatsapp.factory import get_whatsapp_provider
from ai.whatsapp.mock import MockWhatsAppProvider
from ai.whatsapp.meta import MetaWhatsAppProvider

class WhatsAppProviderTests(SimpleTestCase):

    def test_get_whatsapp_provider_returns_mock_provider(self):
        provider = get_whatsapp_provider("mock")

        self.assertIsInstance(
            provider,
            MockWhatsAppProvider,
        )

        self.assertIsInstance(
            provider,
            WhatsAppProvider,
        )

    def test_get_whatsapp_provider_uses_configured_provider(self):
        with patch(
            "ai.whatsapp.factory.MetaWhatsAppProvider"
        ) as mock_provider:
            provider = get_whatsapp_provider()

        mock_provider.assert_called_once_with()
        self.assertEqual(
            provider,
            mock_provider.return_value,
        )    

    def test_get_whatsapp_provider_returns_meta_provider(self):
        with patch(
            "ai.whatsapp.factory.MetaWhatsAppProvider"
        ) as mock_provider:
            provider = get_whatsapp_provider("meta")

        mock_provider.assert_called_once_with()
        self.assertEqual(
            provider,
            mock_provider.return_value,
        )    

    def test_get_whatsapp_provider_returns_mock_provider_when_explicitly_requested(
        self,
    ):
        provider = get_whatsapp_provider("mock")

        self.assertIsInstance(
            provider,
            MockWhatsAppProvider,
        )

    def test_get_whatsapp_provider_accepts_provider_name_case_insensitively(
        self,
    ):
        provider = get_whatsapp_provider(" MOCK ")

        self.assertIsInstance(
            provider,
            MockWhatsAppProvider,
        )

    def test_get_whatsapp_provider_rejects_empty_provider_name(self):
        with self.assertRaises(ValueError) as context:
            get_whatsapp_provider("   ")

        self.assertEqual(
            str(context.exception),
            "WhatsApp provider name cannot be empty.",
        )

    def test_get_whatsapp_provider_rejects_unsupported_provider(self):
        with self.assertRaises(ValueError) as context:
            get_whatsapp_provider("unsupported")

        self.assertEqual(
            str(context.exception),
            "Unsupported WhatsApp provider: unsupported",
        )

    def test_mock_whatsapp_provider_sends_message(self):
        provider = MockWhatsAppProvider()

        result = provider.send_message(
            "919876543210",
            "Hello from AI assistant",
        )

        self.assertEqual(
            result,
            {
                "success": True,
                "recipient": "919876543210",
                "message": "Hello from AI assistant",
            },
        )

    def test_mock_whatsapp_provider_strips_recipient_and_message(self):
        provider = MockWhatsAppProvider()

        result = provider.send_message(
            "  919876543210  ",
            "  Hello from AI assistant  ",
        )

        self.assertEqual(
            result["recipient"],
            "919876543210",
        )

        self.assertEqual(
            result["message"],
            "Hello from AI assistant",
        )

    def test_mock_whatsapp_provider_rejects_empty_recipient(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.send_message(
                "   ",
                "Hello",
            )

        self.assertEqual(
            str(context.exception),
            "Recipient cannot be empty.",
        )

    def test_mock_whatsapp_provider_rejects_empty_message(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.send_message(
                "919876543210",
                "   ",
            )

        self.assertEqual(
            str(context.exception),
            "Message cannot be empty.",
        )    

    def test_mock_whatsapp_provider_verifies_webhook(self):
        provider = MockWhatsAppProvider()

        result = provider.verify_webhook(
            "subscribe",
            "test-token",
            "test-challenge",
        )

        self.assertEqual(
            result,
            "test-challenge",
        )

    def test_mock_whatsapp_provider_strips_webhook_values(self):
        provider = MockWhatsAppProvider()

        result = provider.verify_webhook(
            "  subscribe  ",
            "  test-token  ",
            "  test-challenge  ",
        )

        self.assertEqual(
            result,
            "  test-challenge  ",
        )

    def test_mock_whatsapp_provider_rejects_empty_webhook_mode(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.verify_webhook(
                "   ",
                "test-token",
                "test-challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook mode cannot be empty.",
        )

    def test_mock_whatsapp_provider_rejects_empty_webhook_token(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.verify_webhook(
                "subscribe",
                "   ",
                "test-challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook token cannot be empty.",
        )

    def test_mock_whatsapp_provider_rejects_empty_webhook_challenge(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.verify_webhook(
                "subscribe",
                "test-token",
                "   ",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook challenge cannot be empty.",
        )

    def test_mock_whatsapp_provider_parses_webhook_message(self):
        provider = MockWhatsAppProvider()

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

    def test_mock_whatsapp_provider_returns_empty_for_status_payload(self):
        provider = MockWhatsAppProvider()

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

    def test_mock_whatsapp_provider_ignores_non_text_message(self):
        provider = MockWhatsAppProvider()

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
                                        "id": "wamid.image123",
                                        "type": "image",
                                        "image": {
                                            "id": "media123",
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

        self.assertEqual(result, {})          
            
    def test_mock_whatsapp_provider_rejects_non_dictionary_payload(self):
        provider = MockWhatsAppProvider()

        with self.assertRaises(ValueError) as context:
            provider.parse_webhook_message(
                "invalid payload",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook payload must be a dictionary.",
        )

    def test_mock_whatsapp_provider_accepts_empty_dictionary_payload(self):
        provider = MockWhatsAppProvider()

        result = provider.parse_webhook_message({})

        self.assertEqual(
            result,
            {},
        )    