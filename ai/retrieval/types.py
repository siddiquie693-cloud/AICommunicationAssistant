from dataclasses import dataclass

@dataclass(frozen=True)
class RetrievalResult:
    """
    Represents a single retrieved knowledge passage.
    """

    content: str
    score: float