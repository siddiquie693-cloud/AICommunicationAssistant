
from ai.android.registry_types import (
    ActionDefinition,
    ActionValidationResult,
)
from ai.safety.types import SafetyLevel


class ActionRegistry:
    """
    Maintains the supported NIRA actions and validates planned actions.

    This registry validates actions only. It does not authorize or execute them.
    """

    def __init__(self):
        self._actions: dict[str, ActionDefinition] = {}

    def register(self, definition: ActionDefinition) -> None:
        if not isinstance(definition, ActionDefinition):
            raise TypeError(
                "definition must be an ActionDefinition."
            )

        if not isinstance(definition.name, str) or not definition.name.strip():
            raise ValueError("Action name must be a non-empty string.")

        if definition.name in self._actions:
            raise ValueError(
                f"Action is already registered: {definition.name}."
            )

        if not isinstance(definition.risk_level, SafetyLevel):
            raise TypeError("risk_level must be a SafetyLevel.")

        required = definition.required_parameters
        optional = definition.optional_parameters

        if not isinstance(required, tuple) or not isinstance(optional, tuple):
            raise TypeError("Parameter definitions must be tuples.")

        all_parameters = required + optional

        if any(
            not isinstance(parameter, str) or not parameter.strip()
            for parameter in all_parameters
        ):
            raise ValueError("Parameter names must be non-empty strings.")

        if len(set(all_parameters)) != len(all_parameters):
            raise ValueError(
                "Required and optional parameters must be unique."
            )

        if not isinstance(definition.parameter_types, dict):
            raise TypeError("parameter_types must be a dictionary.")

        for name, parameter_type in definition.parameter_types.items():
            if name not in all_parameters:
                raise ValueError(
                    f"Type declared for an undefined parameter: {name}."
                )

            if not isinstance(parameter_type, type):
                raise TypeError(
                    f"Parameter type for {name} must be a type."
                )

        self._actions[definition.name] = definition

    def get(self, action_name: str) -> ActionDefinition | None:
        if not isinstance(action_name, str):
            raise TypeError("action_name must be a string.")

        return self._actions.get(action_name)

    def validate(
        self,
        action_name: str,
        parameters: dict,
    ) -> ActionValidationResult:

        if not isinstance(action_name, str) or not action_name.strip():
            raise ValueError("action_name must be a non-empty string.")

        if not isinstance(parameters, dict):
            raise TypeError("parameters must be a dictionary.")

        definition = self.get(action_name)

        if definition is None:
            return ActionValidationResult(
                is_valid=False,
                action_name=action_name,
                errors=(f"Unregistered action: {action_name}.",),
            )

        errors = []

        allowed_parameters = (
            set(definition.required_parameters)
            | set(definition.optional_parameters)
        )

        for parameter in definition.required_parameters:
            value = parameters.get(parameter)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                errors.append(
                    f"Missing required parameter: {parameter}."
                )

        if action_name == "send_message":
            has_message = any(
                isinstance(parameters.get(key), str)
                and parameters[key].strip()
                for key in ("request", "content")
            )

            if not has_message:
                errors.append(
                    "A non-empty request or content parameter is required."
                )        

        for parameter in parameters:
            if parameter.startswith("_"):
                continue

            if parameter not in allowed_parameters:
                errors.append(
                    f"Unsupported parameter: {parameter}."
                )

        for parameter, expected_type in definition.parameter_types.items():
            if parameter not in parameters:
                continue

            value = parameters[parameter]

            if not isinstance(value, expected_type):
                errors.append(
                    f"Parameter {parameter} must be of type "
                    f"{expected_type.__name__}."
                )

        return ActionValidationResult(
            is_valid=not errors,
            action_name=action_name,
            errors=tuple(errors),
            risk_level=definition.risk_level,
            validated_parameters={
                key: value
                for key, value in parameters.items()
                if key in allowed_parameters
            },
        )