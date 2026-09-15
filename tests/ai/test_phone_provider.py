from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from ai.phone.exceptions import (
    PhoneProviderError,
    PhoneWebhookError,
)
from ai.phone.factory import get_phone_provider
from ai.phone.mock import MockPhoneProvider
from ai.phone.service import PhoneService
from ai.phone.twilio import TwilioPhoneProvider


class MockPhoneProviderTests(SimpleTestCase):
    def setUp(self):
        self.provider = MockPhoneProvider()
        self.service = PhoneService(self.provider)

    def test_make_call(self):
        result = self.service.make_call(
            "+919630102780",
            "<Response><Say>Hello</Say></Response>",
        )

        self.assertEqual(result["provider"], "mock")
        self.assertEqual(result["recipient"], "+919630102780")
        self.assertEqual(result["status"], "queued")

    def test_make_call_rejects_empty_recipient(self):
        with self.assertRaises(ValueError):
            self.service.make_call(
                "",
                "<Response><Say>Hello</Say></Response>",
            )

    def test_make_call_rejects_empty_twiml(self):
        with self.assertRaises(ValueError):
            self.service.make_call(
                "+919630102780",
                "",
            )

    def test_handle_incoming_call(self):
        result = self.service.handle_incoming_call(
            {
                "From": "+919630102780",
                "To": "+18005551234",
                "CallSid": "CA123",
                "SpeechResult": "Hello AI",
            }
        )

        self.assertEqual(
            result,
            {
                "caller": "+919630102780",
                "called_number": "+18005551234",
                "call_sid": "CA123",
                "speech": "Hello AI",
            },
        )

    def test_handle_incoming_call_rejects_invalid_payload(self):
        with self.assertRaises(ValueError):
            self.service.handle_incoming_call("invalid")

    def test_generate_call_response(self):
        result = self.service.generate_call_response(
            "Hello from AI"
        )

        self.assertEqual(
            result,
            {
                "provider": "mock",
                "text": "Hello from AI",
            },
        )

    def test_generate_call_response_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            self.service.generate_call_response("")


class TwilioPhoneProviderTests(SimpleTestCase):
    def test_provider_requires_account_sid(self):
        with self.assertRaisesMessage(
            ValueError,
            "Twilio Account SID is required.",
        ):
            TwilioPhoneProvider(
                account_sid="",
                auth_token="auth",
                phone_number="+18005551234",
            )

    def test_provider_requires_auth_token(self):
        with self.assertRaisesMessage(
            ValueError,
            "Twilio Auth Token is required.",
        ):
            TwilioPhoneProvider(
                account_sid="AC123",
                auth_token="",
                phone_number="+18005551234",
            )

    def test_provider_requires_phone_number(self):
        with self.assertRaisesMessage(
            ValueError,
            "Twilio phone number is required.",
        ):
            TwilioPhoneProvider(
                account_sid="AC123",
                auth_token="auth",
                phone_number="",
            )

    @patch("ai.phone.twilio.Client")
    def test_provider_initializes_with_credentials(
        self,
        mock_client,
    ):
        provider = TwilioPhoneProvider(
            account_sid="AC123",
            auth_token="auth",
            phone_number="+18005551234",
        )

        self.assertEqual(
            provider.account_sid,
            "AC123",
        )
        self.assertEqual(
            provider.auth_token,
            "auth",
        )
        self.assertEqual(
            provider.phone_number,
            "+18005551234",
        )
        mock_client.assert_called_once_with(
            "AC123",
            "auth",
        )

    @patch("ai.phone.twilio.Client")
    def test_make_call(self, mock_client):
        mock_call = mock_client.return_value.calls.create.return_value
        mock_call.sid = "CA123"
        mock_call.status = "queued"

        provider = TwilioPhoneProvider(
            account_sid="AC123",
            auth_token="auth",
            phone_number="+18005551234",
        )

        result = provider.make_call(
            "+919630102780",
            "<Response><Say>Hello</Say></Response>",
        )

        mock_client.return_value.calls.create.assert_called_once_with(
            to="+919630102780",
            from_="+18005551234",
            twiml="<Response><Say>Hello</Say></Response>",
        )

        self.assertEqual(
            result,
            {
                "provider": "twilio",
                "call_sid": "CA123",
                "status": "queued",
                "recipient": "+919630102780",
            },
        )

    @patch("ai.phone.twilio.Client")
    def test_make_call_wraps_provider_error(
        self,
        mock_client,
    ):
        mock_client.return_value.calls.create.side_effect = (
            RuntimeError("Twilio failure")
        )

        provider = TwilioPhoneProvider(
            account_sid="AC123",
            auth_token="auth",
            phone_number="+18005551234",
        )

        with self.assertRaises(PhoneProviderError):
            provider.make_call(
                "+919630102780",
                "<Response><Say>Hello</Say></Response>",
            )

    def test_generate_call_response(self):
        provider = object.__new__(TwilioPhoneProvider)

        result = provider.generate_call_response(
            "Hello from AI"
        )

        self.assertIn("<Response>", result)
        self.assertIn("<Say>Hello from AI</Say>", result)
        self.assertIn("</Response>", result)

    def test_generate_call_response_rejects_empty_text(self):
        provider = object.__new__(TwilioPhoneProvider)

        with self.assertRaises(ValueError):
            provider.generate_call_response("")

    def test_handle_incoming_call(self):
        provider = object.__new__(TwilioPhoneProvider)

        result = provider.handle_incoming_call(
            {
                "From": "+919630102780",
                "To": "+18005551234",
                "CallSid": "CA123",
                "SpeechResult": "Hello AI",
            }
        )

        self.assertEqual(
            result,
            {
                "caller": "+919630102780",
                "called_number": "+18005551234",
                "call_sid": "CA123",
                "speech": "Hello AI",
            },
        )

    def test_handle_incoming_call_requires_caller(self):
        provider = object.__new__(TwilioPhoneProvider)

        with self.assertRaises(PhoneWebhookError):
            provider.handle_incoming_call(
                {
                    "From": "",
                    "To": "+18005551234",
                    "CallSid": "CA123",
                    "SpeechResult": "Hello AI",
                }
            )

    def test_handle_incoming_call_requires_call_sid(self):
        provider = object.__new__(TwilioPhoneProvider)

        with self.assertRaises(PhoneWebhookError):
            provider.handle_incoming_call(
                {
                    "From": "+919630102780",
                    "To": "+18005551234",
                    "CallSid": "",
                    "SpeechResult": "Hello AI",
                }
            )


class PhoneFactoryTests(SimpleTestCase):
    @override_settings(PHONE_PROVIDER="mock")
    def test_default_provider_is_mock(self):
        provider = get_phone_provider()

        self.assertIsInstance(
            provider,
            MockPhoneProvider,
        )

    def test_explicit_mock_provider(self):
        provider = get_phone_provider("mock")

        self.assertIsInstance(
            provider,
            MockPhoneProvider,
        )

    def test_empty_provider_name_rejected(self):
        with self.assertRaises(ValueError):
            get_phone_provider("")

    def test_unsupported_provider_rejected(self):
        with self.assertRaises(ValueError):
            get_phone_provider("unsupported")