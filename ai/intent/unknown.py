from ai.intent.categories import IntentCategory
from ai.intent.types import Intent


def create_unknown_intent() -> Intent:
    """
    Create a standardized intent for unsupported or unrecognized requests.
    """
    return Intent(
        name=IntentCategory.UNKNOWN.value,
        parameters={},
    )