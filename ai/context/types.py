from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Context:
    """
    Structured context available to NIRA for reasoning.
    """

    conversation: list[dict[str, Any]] = field(default_factory=list)
    memory: list[dict[str, Any]] = field(default_factory=list)
    person: dict[str, Any] | None = None
    knowledge: str = ""
    profile: dict[str, Any] | None = None