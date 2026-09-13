class WhatsAppError(Exception):
    """Base exception for WhatsApp integration errors."""


class WhatsAppProviderError(WhatsAppError):
    """Raised when the WhatsApp provider fails."""


class WhatsAppWebhookError(WhatsAppError):
    """Raised when WhatsApp webhook processing fails."""