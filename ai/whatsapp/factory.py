from ai.whatsapp.base import WhatsAppProvider
from ai.whatsapp.mock import MockWhatsAppProvider


def get_whatsapp_provider(
    provider_name: str | None = None,
) -> WhatsAppProvider:
    normalized_provider = (
        provider_name.strip().lower()
        if provider_name is not None
        else "mock"
    )

    if not normalized_provider:
        raise ValueError("WhatsApp provider name cannot be empty.")

    if normalized_provider == "mock":
        return MockWhatsAppProvider()

    raise ValueError(
        f"Unsupported WhatsApp provider: {provider_name}"
    )