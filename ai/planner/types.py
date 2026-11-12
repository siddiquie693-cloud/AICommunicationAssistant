from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class PlannedAction:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    action_id: str | None = None
    depends_on: tuple[str, ...] = ()
    description: str = ""


@dataclass(frozen=True)
class ActionPlan:
    actions: list[PlannedAction] = field(default_factory=list)
    requires_clarification: bool = False
    clarification_question: str | None = None
    errors: tuple[str, ...] = ()