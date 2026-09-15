from ai.phone.base import PhoneProvider


class MockPhoneProvider(PhoneProvider):
    def make_call(self, recipient: str, twiml: str):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not twiml or not twiml.strip():
            raise ValueError("TwiML cannot be empty.")

        return {
            "provider": "mock",
            "recipient": recipient.strip(),
            "twiml": twiml.strip(),
            "status": "queued",
        }

    def handle_incoming_call(self, payload: dict):
        if not isinstance(payload, dict):
            raise ValueError("Phone call payload must be a dictionary.")

        return {
            "caller": str(payload.get("From", "")).strip(),
            "called_number": str(payload.get("To", "")).strip(),
            "call_sid": str(payload.get("CallSid", "")).strip(),
            "speech": str(payload.get("SpeechResult", "")).strip(),
        }

    def generate_call_response(self, text: str):
        if not text or not text.strip():
            raise ValueError("Call response text cannot be empty.")

        return {
            "provider": "mock",
            "text": text.strip(),
        }