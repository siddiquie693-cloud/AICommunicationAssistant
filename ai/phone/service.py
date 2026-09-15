from ai.phone.base import PhoneProvider


class PhoneService:
    def __init__(self, provider: PhoneProvider):
        self.provider = provider

    def make_call(self, recipient: str, twiml: str):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not twiml or not twiml.strip():
            raise ValueError("TwiML cannot be empty.")

        return self.provider.make_call(
            recipient.strip(),
            twiml.strip(),
        )

    def handle_incoming_call(self, payload: dict):
        if not isinstance(payload, dict):
            raise ValueError(
                "Phone call payload must be a dictionary."
            )

        return self.provider.handle_incoming_call(payload)

    def generate_call_response(self, text: str):
        if not text or not text.strip():
            raise ValueError(
                "Call response text cannot be empty."
            )

        return self.provider.generate_call_response(
            text.strip(),
        )