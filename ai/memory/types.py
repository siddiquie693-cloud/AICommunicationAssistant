from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryQuery:
    """
    Structured request for retrieving relevant personal memory.
    """

    text: str
    user_id: int
    limit: int = 5


@dataclass(frozen=True)
class MemoryResult:
    """
    Structured personal memory returned to the Context Engine.
    """

    content: str
    metadata: dict[str, Any]