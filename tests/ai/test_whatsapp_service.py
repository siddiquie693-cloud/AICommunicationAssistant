from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.whatsapp.service import WhatsAppService


class WhatsAppServiceTests(SimpleTestCase):

    def test_send_message_delegates_to_provider(self):
        provider = Mock()

        provider.send_message.return_value = {
            "success": True,
            "recipient": "919876543210",
            "message": "Hello",
        }

        service = WhatsAppService(provider)

        result = service.send_message(
            "919876543210",
            "Hello",
        )

        self.assertEqual(
            result,
            provider.send_message.return_value,
        )

        provider.send_message.assert_called_once_with(
            "919876543210",
            "Hello",
        )

    def test_send_message_strips_recipient_and_message(self):
        provider = Mock()
        service = WhatsAppService(provider)

        service.send_message(
            "  919876543210  ",
            "  Hello  ",
        )

        provider.send_message.assert_called_once_with(
            "919876543210",
            "Hello",
        )

    def test_send_message_rejects_empty_recipient(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.send_message(
                "   ",
                "Hello",
            )

        self.assertEqual(
            str(context.exception),
            "Recipient cannot be empty.",
        )

    def test_send_message_rejects_empty_message(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.send_message(
                "919876543210",
                "   ",
            )

        self.assertEqual(
            str(context.exception),
            "Message cannot be empty.",
        )

    def test_verify_webhook_delegates_to_provider(self):
        provider = Mock()

        provider.verify_webhook.return_value = "challenge"

        service = WhatsAppService(provider)

        result = service.verify_webhook(
            "subscribe",
            "test-token",
            "challenge",
        )

        self.assertEqual(
            result,
            "challenge",
        )

        provider.verify_webhook.assert_called_once_with(
            "subscribe",
            "test-token",
            "challenge",
        )

    def test_verify_webhook_strips_values(self):
        provider = Mock()
        service = WhatsAppService(provider)

        service.verify_webhook(
            "  subscribe  ",
            "  test-token  ",
            "  challenge  ",
        )

        provider.verify_webhook.assert_called_once_with(
            "subscribe",
            "test-token",
            "challenge",
        )

    def test_verify_webhook_rejects_empty_mode(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.verify_webhook(
                "   ",
                "test-token",
                "challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook mode cannot be empty.",
        )

    def test_verify_webhook_rejects_empty_token(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.verify_webhook(
                "subscribe",
                "   ",
                "challenge",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook token cannot be empty.",
        )

    def test_verify_webhook_rejects_empty_challenge(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.verify_webhook(
                "subscribe",
                "test-token",
                "   ",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook challenge cannot be empty.",
        )

    def test_parse_webhook_message_delegates_to_provider(self):
        provider = Mock()

        payload = {
            "object": "whatsapp_business_account",
        }

        provider.parse_webhook_message.return_value = payload

        service = WhatsAppService(provider)

        result = service.parse_webhook_message(payload)

        self.assertEqual(
            result,
            payload,
        )

        provider.parse_webhook_message.assert_called_once_with(
            payload,
        )

    def test_parse_webhook_message_rejects_non_dictionary_payload(self):
        provider = Mock()
        service = WhatsAppService(provider)

        with self.assertRaises(ValueError) as context:
            service.parse_webhook_message(
                "invalid payload",
            )

        self.assertEqual(
            str(context.exception),
            "Webhook payload must be a dictionary.",
        )    