
from dataclasses import dataclass

from ai.intent.types import Intent
from ai.intent.mappings import INTENT_CATEGORY_MAPPING


@dataclass(frozen=True)
class IntentValidationResult:
    is_valid: bool
    intent: Intent
    errors: tuple[str, ...] = ()


class IntentValidator:
    """
    Validates detected intents before they can proceed to planning.
    """

    REQUIRED_PARAMETERS = {
        "call_person": ("recipient",),
        "send_message": ("request",),
        "open_app": ("app",),
        "create_reminder": ("request",),
        "navigate": ("location",),
        "play_media": ("request",),
        "check_notifications": (),
    }

    def validate(self, intent: Intent) -> IntentValidationResult:
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent.")

        if intent.name not in INTENT_CATEGORY_MAPPING:
            return IntentValidationResult(
                is_valid=False,
                intent=intent,
                errors=("Unsupported intent name.",),
            )

        if intent.name == "unknown":
            return IntentValidationResult(
                is_valid=False,
                intent=intent,
                errors=("Intent is not recognized.",),
            )

        errors = []

        required_parameters = self.REQUIRED_PARAMETERS[intent.name]

        for parameter in required_parameters:
            value = intent.parameters.get(parameter)

            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"Missing or invalid required parameter: {parameter}."
                )

        return IntentValidationResult(
            is_valid=not errors,
            intent=intent,
            errors=tuple(errors),
        )