from ai.whatsapp.base import WhatsAppProvider


class WhatsAppService:
    def __init__(self, provider: WhatsAppProvider):
        self.provider = provider

    def send_message(
        self,
        recipient: str,
        message: str,
    ):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        return self.provider.send_message(
            recipient.strip(),
            message.strip(),
        )

    def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
    ):
        if not mode or not mode.strip():
            raise ValueError("Webhook mode cannot be empty.")

        if not token or not token.strip():
            raise ValueError("Webhook token cannot be empty.")

        if not challenge or not challenge.strip():
            raise ValueError("Webhook challenge cannot be empty.")

        return self.provider.verify_webhook(
            mode.strip(),
            token.strip(),
            challenge.strip(),
        )

    def parse_webhook_message(
        self,
        payload: dict,
    ):
        if not isinstance(payload, dict):
            raise ValueError(
                "Webhook payload must be a dictionary."
            )

        return self.provider.parse_webhook_message(
            payload,
        )