
from dataclasses import dataclass, field
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
            raise TypeError("text must be string.")

        if not self.text.strip():
            raise ValueError("text must not be empty.")

        if not isinstance(self.source, str):
            raise TypeError("source must be a string.")

        if not self.source.strip():
            raise ValueError("source must not be empty.")

        if self.language is not None and not isinstance(
            self.language,
            str,
        ):
            raise TypeError("language must be a string or None.")


@dataclass(frozen=True)
class PendingActionConfirmation:
    """
    Represents an action waiting for explicit user approval.
    """

    confirmation_id: str
    action_name: str
    parameters: dict[str, Any]
    reason: str

    def __post_init__(self):
        if not isinstance(self.confirmation_id, str):
            raise TypeError("confirmation_id must be a string.")

        if not self.confirmation_id.strip():
            raise ValueError("confirmation_id must not be empty.")

        if not isinstance(self.action_name, str):
            raise TypeError("action_name must be a string.")

        if not self.action_name.strip():
            raise ValueError("action_name must not be empty.")

        if not isinstance(self.parameters, dict):
            raise TypeError("parameters must be a dictionary.")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string.")


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
    validation_result: Any = None
    pending_confirmations: list[PendingActionConfirmation] = field(
        default_factory=list
    )