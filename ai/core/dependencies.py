
from dataclasses import dataclass
from typing import Any

from ai.safety.service import SafetyEngine


@dataclass(frozen=True)
class NIRADependencies:
    """Holds the dependencies required by NIRA Brain."""

    ai_service: Any
    context_engine: Any
    intent_engine: Any
    action_planner: Any
    safety_engine: Any = None

    android_action_engine: Any = None
    person_identity_resolver: Any = None
    safety_request_builder: Any = None
    confirmation_store: Any = None
    safety_evaluator: Any = None

    def validate_for_brain(self) -> None:
        """Validate dependencies required for Brain processing."""

        required = {
            "ai_service": self.ai_service,
            "context_engine": self.context_engine,
            "intent_engine": self.intent_engine,
            "action_planner": self.action_planner,
        }

        missing = [
            name
            for name, dependency in required.items()
            if dependency is None
        ]

        if missing:
            raise ValueError(
                "Missing required NIRA Brain dependencies: "
                + ", ".join(missing)
            )

        if self.safety_engine is not None and self.safety_evaluator is not None:
            raise ValueError(
                "Provide either safety_engine or safety_evaluator, not both."
            )

        if self.safety_engine is None and self.safety_evaluator is None:
            raise ValueError(
                "A safety_engine or safety_evaluator is required."
            )

    def validate_for_phone_actions(self) -> None:
        """Validate dependencies required for phone action execution."""

        self.validate_for_brain()

        if self.android_action_engine is None:
            raise ValueError(
                "Android Action Engine is required "
                "for phone action execution."
            )

    def get_brain_kwargs(self) -> dict[str, Any]:
        """Return configured dependencies for NIRABrain."""

        self.validate_for_brain()

        safety_engine = self.safety_engine

        if safety_engine is None:
            safety_engine = SafetyEngine(self.safety_evaluator)

        dependencies = {
            "context_engine": self.context_engine,
            "intent_engine": self.intent_engine,
            "action_planner": self.action_planner,
            "safety_engine": safety_engine,
            "android_action_engine": self.android_action_engine,
        }

        if self.person_identity_resolver is not None:
            dependencies["person_identity_resolver"] = (
                self.person_identity_resolver
            )

        if self.safety_request_builder is not None:
            dependencies["safety_request_builder"] = (
                self.safety_request_builder
            )

        if self.confirmation_store is not None:
            dependencies["confirmation_store"] = (
                self.confirmation_store
            )

        return dependencies