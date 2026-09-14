import httpx2
from django.conf import settings

from ai.whatsapp.base import WhatsAppProvider
from ai.whatsapp.exceptions import (
    WhatsAppProviderError,
    WhatsAppWebhookError,
)


class MetaWhatsAppProvider(WhatsAppProvider):
    """
    WhatsApp Cloud API provider using Meta's Graph API.
    """

    def __init__(
        self,
        access_token=None,
        phone_number_id=None,
        api_version=None,
    ):
        self.access_token = (
            access_token
            if access_token is not None
            else settings.WHATSAPP_ACCESS_TOKEN
        )
        self.phone_number_id = (
            phone_number_id
            if phone_number_id is not None
            else settings.WHATSAPP_PHONE_NUMBER_ID
        )
        self.api_version = (
            api_version
            if api_version is not None
            else settings.WHATSAPP_API_VERSION
        )

        if not self.access_token:
            raise ValueError(
                "WhatsApp access token is not configured."
            )

        if not self.phone_number_id:
            raise ValueError(
                "WhatsApp phone number ID is not configured."
            )

        if not self.api_version:
            raise ValueError(
                "WhatsApp API version is not configured."
            )

    @property
    def messages_url(self):
        return (
            f"https://graph.facebook.com/"
            f"{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )

    def send_message(
        self,
        recipient: str,
        message: str,
    ):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient.strip(),
            "type": "text",
            "text": {
                "body": message.strip(),
            },
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx2.post(
                self.messages_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
        except Exception as exc:
            raise WhatsAppProviderError(
                "Unable to connect to WhatsApp Cloud API."
            ) from exc

        if response.status_code >= 400:
            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text    
            raise WhatsAppProviderError(
                f"WhatsApp Cloud API returned an error "
                f"(status={response.status_code}): {error_data}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise WhatsAppProviderError(
                "WhatsApp Cloud API returned an invalid response."
            ) from exc

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

        if mode.strip() != "subscribe":
            raise WhatsAppWebhookError(
                "Invalid webhook verification mode."
            )

        expected_token = getattr(
            settings,
            "WHATSAPP_VERIFY_TOKEN",
            "",
        )

        if not expected_token or token.strip() != expected_token:
            raise WhatsAppWebhookError(
                "Invalid webhook verification token."
            )

        return challenge.strip()

    def parse_webhook_message(
        self,
        payload: dict,
    ):
        if not isinstance(payload, dict):
            raise ValueError(
                "Webhook payload must be a dictionary."
            )

        if not payload:
            return {}

        entries = payload.get("entry")

        if not isinstance(entries, list) or not entries:
            return {}

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            changes = entry.get("changes")

            if not isinstance(changes, list):
                continue

            for change in changes:
                if not isinstance(change, dict):
                    continue

                value = change.get("value")

                if not isinstance(value, dict):
                    continue

                messages = value.get("messages")

                if not isinstance(messages, list):
                    continue

                for message in messages:
                    if not isinstance(message, dict):
                        continue

                    sender = message.get("from")
                    message_id = message.get("id")
                    message_type = message.get("type")

                    if message_type != "text":
                        continue

                    text = message.get("text")

                    if not isinstance(text, dict):
                        continue

                    body = text.get("body")

                    if not sender or not message_id:
                        continue

                    if not isinstance(body, str) or not body.strip():
                        continue

                    return {
                        "sender": sender,
                        "message": body.strip(),
                        "message_id": message_id,
                    }

        return {}