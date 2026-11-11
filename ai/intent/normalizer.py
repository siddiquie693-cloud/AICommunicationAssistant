from ai.intent.types import Intent


def normalize_intent(intent: Intent) -> Intent:
    """
    Normalize an Intent without modifying its meaning.
    """
    if not isinstance(intent, Intent):
        raise TypeError("intent must be an Intent.")

    normalized_name = intent.name.strip().lower()

    return Intent(
        name=normalized_name,
        parameters=intent.parameters,
    )