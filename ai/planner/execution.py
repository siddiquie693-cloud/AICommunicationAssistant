
from ai.planner.types import ActionPlan


class ActionExecutionOrder:
    """
    Provides dependency-aware action ordering.
    Does not execute or authorize actions.
    """

    def get_order(self, plan: ActionPlan) -> tuple[str, ...]:
        if not isinstance(plan, ActionPlan):
            raise TypeError("plan must be an ActionPlan.")

        completed = set()
        ordered = []

        for action in plan.actions:
            if not action.action_id:
                raise ValueError("Every action requires an action ID.")

            if not set(action.depends_on).issubset(completed):
                raise ValueError(
                    f"Dependencies are not satisfied for {action.action_id}."
                )

            ordered.append(action.action_id)
            completed.add(action.action_id)

        return tuple(ordered)
