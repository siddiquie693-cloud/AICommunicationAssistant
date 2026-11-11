from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Intent:
    """
    Structured representation of an intent understood by NIRA.
    """

    name: str
    parameters: dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")

        if not self.name.strip():
            raise ValueError("name must not be empty.")

        if not isinstance(self.parameters, dict):
            raise TypeError("parameters must be a dictionary.")