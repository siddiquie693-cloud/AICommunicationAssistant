from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Intent:
    """
    Structured representation of an intent understood by NIRA.
    """

    name: str
    parameters: dict[str, Any]