from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.communication.service import CommunicationEngine
from ai.communication.types import (
    CommunicationRequest,
    CommunicationResult,
)


class CommunicationEngineTests(SimpleTestCase):

    def test_communication_engine_delegates_send_to_adapter(self):
        adapter = Mock()

        expected_result = CommunicationResult(
            success=True,
            channel="whatsapp",
            recipient="+911234567890",
            message="Message sent.",
        )

        adapter.send.return_value = expected_result

        engine = CommunicationEngine(adapter)

        request = CommunicationRequest(
            channel="whatsapp",
            recipient="+911234567890",
            content="Hello",
        )

        result = engine.send(request)

        self.assertEqual(result, expected_result)
        adapter.send.assert_called_once_with(request)

    def test_communication_engine_rejects_non_communication_request(self):
        adapter = Mock()
        engine = CommunicationEngine(adapter)

        with self.assertRaises(TypeError):
            engine.send("Hello")

    def test_communication_engine_rejects_invalid_adapter_result(self):
        adapter = Mock()
        adapter.send.return_value = "Message sent."

        engine = CommunicationEngine(adapter)

        request = CommunicationRequest(
            channel="whatsapp",
            recipient="+911234567890",
            content="Hello",
        )

        with self.assertRaises(TypeError):
            engine.send(request)