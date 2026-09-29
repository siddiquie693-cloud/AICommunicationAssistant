from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlannedAction:
    """
    A single action proposed by the NIRA Action Planner.
    """

    name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionPlan:
    """
    Ordered actions produced from an understood intent.
    """

    actions: list[PlannedAction] = field(default_factory=list)