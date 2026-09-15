class PhoneError(Exception):
    """Base exception for phone integration errors."""


class PhoneProviderError(PhoneError):
    """Raised when the phone provider fails."""


class PhoneWebhookError(PhoneError):
    """Raised when phone webhook processing fails."""