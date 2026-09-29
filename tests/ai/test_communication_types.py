from django.test import SimpleTestCase

from ai.communication.types import (
    CommunicationRequest,
    CommunicationResult,
)


class CommunicationRequestTests(SimpleTestCase):

    def test_communication_request_stores_all_fields(self):
        request = CommunicationRequest(
            channel="whatsapp",
            recipient="+911234567890",
            content="Hello",
            metadata={"language": "en"},
        )

        self.assertEqual(request.channel, "whatsapp")
        self.assertEqual(request.recipient, "+911234567890")
        self.assertEqual(request.content, "Hello")
        self.assertEqual(
            request.metadata,
            {"language": "en"},
        )

    def test_communication_request_defaults_metadata_to_none(self):
        request = CommunicationRequest(
            channel="sms",
            recipient="+911234567890",
            content="Hello",
        )

        self.assertIsNone(request.metadata)


class CommunicationResultTests(SimpleTestCase):

    def test_communication_result_stores_all_fields(self):
        result = CommunicationResult(
            success=True,
            channel="whatsapp",
            recipient="+911234567890",
            message="Message sent.",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.channel, "whatsapp")
        self.assertEqual(result.recipient, "+911234567890")
        self.assertEqual(result.message, "Message sent.")