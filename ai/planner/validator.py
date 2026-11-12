
from dataclasses import dataclass

from ai.planner.types import ActionPlan, PlannedAction


@dataclass(frozen=True)
class ActionPlanValidationResult:
    is_valid: bool
    errors: tuple[str, ...] = ()


class ActionPlanValidator:
    """
    Validates action IDs, dependencies, and execution ordering.
    """

    def validate(self, plan: ActionPlan) -> ActionPlanValidationResult:
        if not isinstance(plan, ActionPlan):
            raise TypeError("plan must be an ActionPlan.")

        errors = []

        if plan.requires_clarification:
            errors.append("Action plan requires clarification.")

        if plan.errors:
            errors.extend(plan.errors)

        action_positions = {}
        action_ids = set()

        for index, action in enumerate(plan.actions):
            if not isinstance(action, PlannedAction):
                errors.append(
                    f"Invalid action at position {index}."
                )
                continue

            if not isinstance(action.name, str) or not action.name.strip():
                errors.append(
                    f"Action at position {index} has an invalid name."
                )

            if action.action_id is not None:
                if (
                    not isinstance(action.action_id, str)
                    or not action.action_id.strip()
                ):
                    errors.append(
                        f"Action at position {index} has an invalid ID."
                    )
                elif action.action_id in action_ids:
                    errors.append(
                        f"Duplicate action ID: {action.action_id}."
                    )
                else:
                    action_ids.add(action.action_id)
                    action_positions[action.action_id] = index

            if not isinstance(action.depends_on, tuple):
                errors.append(
                    f"Dependencies must be a tuple at position {index}."
                )

        for index, action in enumerate(plan.actions):
            if not isinstance(action, PlannedAction):
                continue

            if not isinstance(action.depends_on, tuple):
                continue

            if action.depends_on and not action.action_id:
                errors.append(
                    f"Action at position {index} requires an action ID "
                    "when it has dependencies."
                )

            for dependency in action.depends_on:
                if not isinstance(dependency, str) or not dependency.strip():
                    errors.append(
                        f"Action at position {index} has an invalid dependency ID."
                    )
                    continue

                if dependency == action.action_id:
                    errors.append(
                        f"Action {action.action_id} cannot depend on itself."
                    )
                    continue

                if dependency not in action_positions:
                    errors.append(
                        f"Unknown dependency ID: {dependency}."
                    )
                    continue

                if action_positions[dependency] >= index:
                    errors.append(
                        f"Dependency {dependency} must appear before "
                        f"action {action.action_id}."
                    )

        return ActionPlanValidationResult(
            is_valid=not errors,
            errors=tuple(errors),
        )
