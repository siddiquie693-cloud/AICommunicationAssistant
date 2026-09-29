from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommunicationRequest:
    """
    Structured communication request handled by NIRA.
    """

    channel: str
    recipient: str
    content: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class CommunicationResult:
    """
    Result returned after a communication operation.
    """

    success: bool
    channel: str
    recipient: str
    message: str