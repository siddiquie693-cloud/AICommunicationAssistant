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