from unittest.mock import patch
from ai.phone.exceptions import PhoneProviderError
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User

class PhoneWebhookAPIViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/phone/webhook/"

        self.user = User.objects.create_user(
            username="phone_test_user",
            email="phone-test@example.com",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=self.user)

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_webhook_success(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.handle_incoming_call.return_value = {
            "caller": "+919630102780",
            "called_number": "+18005551234",
            "call_sid": "CA_TEST_123",
            "speech": "Hello AI",
        }

        response = self.client.post(
            self.url,
            {
                "From": "+919630102780",
                "To": "+18005551234",
                "CallSid": "CA_TEST_123",
                "SpeechResult": "Hello AI",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["payload"]["call_sid"],
            "CA_TEST_123",
        )

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_webhook_invalid_payload(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.handle_incoming_call.side_effect = ValueError(
            "Phone call payload must be a dictionary."
        )

        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "phone_webhook_error",
        )

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_webhook_provider_error(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value
        mock_provider.handle_incoming_call.side_effect = PhoneProviderError(
            "provider failure"
        )

        response = self.client.post(
            self.url,
            {
                "From": "+919630102780",
                "To": "+18005551234",
                "CallSid": "CA_TEST_123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 503)

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_call_success(self, mock_get_provider):
        mock_provider = mock_get_provider.return_value

        mock_provider.generate_call_response.return_value = (
            "<Response><Say><Hello></Say></Response>"
        )
        mock_provider.make_call.return_value = {
            "provider": "mock",
            "recipient": "+919630102780",
            "twiml": "<Response><Say>Hello</Say></Response>",
            "status": "queued",
        }

        response = self.client.post(
            "/api/phone/call/",
            {
                "recipient": "+919630102780",
                "text": "Hello",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["call"]["status"],
            "queued",
        )

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_call_validation_error(self, mock_get_provider):
        response = self.client.post(
            "/api/phone/call/",
            {
                "recipient": "",
                "text": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"]["code"],
            "phone_call_error",
        )

    @patch("conversations.phone_views.get_phone_provider")
    def test_phone_call_provider_error(self, mock_get_provider):
        from ai.phone.exceptions import PhoneProviderError

        mock_provider = mock_get_provider.return_value
        mock_provider.make_call.side_effect = PhoneProviderError(
            "provider failure"
        )

        response = self.client.post(
            "/api/phone/call/",
            {
                "recipient": "+919630102780",
                "text": "Hello",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data["error"]["code"],
            "phone_provider_error",
        )    