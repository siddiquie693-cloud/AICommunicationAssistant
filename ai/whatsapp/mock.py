from ai.whatsapp.base import WhatsAppProvider


class MockWhatsAppProvider(WhatsAppProvider):
    def send_message(
        self,
        recipient: str,
        message: str,
    ):
        if not recipient or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")

        return {
            "success": True,
            "recipient": recipient.strip(),
            "message": message.strip(),
        }

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

        return challenge

    def parse_webhook_message(
        self,
        payload: dict,
    ):
        if not isinstance(payload, dict):
            raise ValueError("Webhook payload must be a dictionary.")

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