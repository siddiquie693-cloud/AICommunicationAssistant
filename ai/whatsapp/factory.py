from ai.whatsapp.base import WhatsAppProvider
from ai.whatsapp.mock import MockWhatsAppProvider
from ai.whatsapp.meta import MetaWhatsAppProvider
from django.conf import settings

def get_whatsapp_provider(
    provider_name: str | None = None,
) -> WhatsAppProvider:
    normalized_provider = (
        provider_name.strip().lower()
        if provider_name is not None
        else settings.WHATSAPP_PROVIDER.strip().lower()
    )

    if not normalized_provider:
        raise ValueError("WhatsApp provider name cannot be empty.")

    if normalized_provider == "mock":
        return MockWhatsAppProvider()

    if normalized_provider == "meta":
        return MetaWhatsAppProvider()

    raise ValueError(
        f"Unsupported WhatsApp provider: {provider_name}"
    )