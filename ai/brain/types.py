from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BrainRequest:
    """
    Structured input received by the NIRA AI Brain.
    """

    text: str
    source: str = "text"
    language: str | None = None

    def __post_init__(self):
        if not isinstance(self.text, str):
            raise TypeError(
                "text must be string."
            )
        if not self.text.strip():
            raise ValueError(
                "text must not be empty."
            )
        if not isinstance(self.source, str):
            raise TypeError(
                "source must be a string."
            )
        if not self.source.strip():
            raise ValueError(
                "source must not be empty."
            )
        if self.language is not None and not isinstance(
            self.language,
            str,
        ):
            raise TypeError(
                "language must be a string or None."
            )

@dataclass(frozen=True)
class BrainPipelineResult:
    """
    Result produced after processing a NIRA action pipeline.
    """

    intent: Any
    context: Any
    action_plan: Any
    safety_results: list[Any]
    action_results: list[Any]