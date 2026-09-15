from django.conf import settings

from ai.phone.base import PhoneProvider
from ai.phone.mock import MockPhoneProvider


def get_phone_provider(
    provider_name: str | None = None,
) -> PhoneProvider:
    normalized_provider = (
        provider_name.strip().lower()
        if provider_name is not None
        else settings.PHONE_PROVIDER.strip().lower()
    )

    if not normalized_provider:
        raise ValueError("Phone provider name cannot be empty.")

    if normalized_provider == "mock":
        return MockPhoneProvider()

    if normalized_provider == "twilio":
        from ai.phone.twilio import TwilioPhoneProvider

        return TwilioPhoneProvider()

    raise ValueError(
        f"Unsupported phone provider: {provider_name}"
    )