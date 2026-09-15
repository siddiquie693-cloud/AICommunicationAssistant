from django.conf import settings
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from ai.phone.base import PhoneProvider
from ai.phone.exceptions import (
    PhoneProviderError,
    PhoneWebhookError,
)


class TwilioPhoneProvider(PhoneProvider):
    def __init__(
        self,
        account_sid=None,
        auth_token=None,
        phone_number=None,
    ):
        self.account_sid = (
            account_sid
            if account_sid is not None
            else settings.TWILIO_ACCOUNT_SID
        )

        self.auth_token = (
            auth_token
            if auth_token is not None
            else settings.TWILIO_AUTH_TOKEN
        )

        self.phone_number = (
            phone_number
            if phone_number is not None
            else settings.TWILIO_PHONE_NUMBER
        )

        if not self.account_sid:
            raise ValueError("Twilio Account SID is required.")

        if not self.auth_token:
            raise ValueError("Twilio Auth Token is required.")

        if not self.phone_number:
            raise ValueError("Twilio phone number is required.")

        self.client = Client(
            self.account_sid,
            self.auth_token,
        )

    def make_call(self, recipient: str, twiml: str):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not twiml or not twiml.strip():
            raise ValueError("TwiML cannot be empty.")

        try:
            call = self.client.calls.create(
                to=recipient.strip(),
                from_=self.phone_number,
                twiml=twiml.strip(),
            )
        except Exception as exc:
            raise PhoneProviderError(
                "Twilio failed to create the phone call."
            ) from exc

        return {
            "provider": "twilio",
            "call_sid": call.sid,
            "status": call.status,
            "recipient": recipient.strip(),
        }

    def handle_incoming_call(self, payload: dict):
        if not isinstance(payload, dict):
            raise ValueError(
                "Phone call payload must be a dictionary."
            )

        caller = str(payload.get("From", "")).strip()
        called_number = str(payload.get("To", "")).strip()
        call_sid = str(payload.get("CallSid", "")).strip()

        if not caller:
            raise PhoneWebhookError(
                "Incoming call caller number is missing."
            )

        if not call_sid:
            raise PhoneWebhookError(
                "Incoming call SID is missing."
            )

        return {
            "caller": caller,
            "called_number": called_number,
            "call_sid": call_sid,
            "speech": str(
                payload.get("SpeechResult", "")
            ).strip(),
        }

    def generate_call_response(self, text: str):
        if not text or not text.strip():
            raise ValueError(
                "Call response text cannot be empty."
            )

        response = VoiceResponse()
        response.say(text.strip())

        return str(response)