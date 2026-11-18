
from dataclasses import dataclass, field
from typing import Any

from ai.safety.types import SafetyLevel


@dataclass(frozen=True)
class ActionDefinition:
    """
    Defines a supported action and its validation requirements.
    """

    name: str
    required_parameters: tuple[str, ...] = ()
    optional_parameters: tuple[str, ...] = ()
    parameter_types: dict[str, type] = field(default_factory=dict)
    risk_level: SafetyLevel = SafetyLevel.MEDIUM


@dataclass(frozen=True)
class ActionValidationResult:
    """
    Result of validating an action against the registry.
    """

    is_valid: bool
    action_name: str
    errors: tuple[str, ...] = ()
    risk_level: SafetyLevel | None = None
    validated_parameters: dict[str, Any] = field(default_factory=dict)