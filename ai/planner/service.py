from ai.intent.types import Intent
from ai.planner.types import ActionPlan


class ActionPlanner:
    """
    Converts an Intent into an ordered ActionPlan.

    The actual planning implementation is injected so that the
    planner remains independent from a specific AI provider.
    """

    def __init__(self, planner):
        self.planner = planner

    def plan(self, intent: Intent) -> ActionPlan:
        """
        Create an action plan from a structured intent.
        """
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent.")

        action_plan = self.planner.plan(intent)

        if not isinstance(action_plan, ActionPlan):
            raise TypeError(
                "planner must return an ActionPlan."
            )

        return action_plan