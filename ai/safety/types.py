from dataclasses import dataclass
from enum import Enum
from typing import Any


class SafetyLevel(str, Enum):
    """
    Risk level assigned to an action.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SafetyDecision(str, Enum):
    """
    Decision produced by the Safety Engine.
    """

    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


@dataclass(frozen=True)
class SafetyRequest:
    """
    Request evaluated by the NIRA Safety Engine.
    """

    action_name: str
    parameters: dict[str, Any]
    risk_level: SafetyLevel


@dataclass(frozen=True)
class SafetyResult:
    """
    Result returned by the NIRA Safety Engine.
    """

    decision: SafetyDecision
    reason: str