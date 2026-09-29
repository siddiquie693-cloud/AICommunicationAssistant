from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AndroidActionRequest:
    """
    Authorized action request sent to the Android Action Engine.
    """

    action_name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AndroidActionResult:
    """
    Result returned after an Android action is processed.
    """

    success: bool
    action_name: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)