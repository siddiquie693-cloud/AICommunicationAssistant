from ai.intent.types import Intent
from ai.planner.types import ActionPlan, PlannedAction


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

class IntentActionPlanner:
    """
    Converts supported NIRA intents into planned Android actions.
    """

    INTENT_ACTION_MAPPING = {
        "call_person": "call_person",
        "send_message": "send_message",
        "open_app": "open_app",
        "create_reminder": "create_reminder",
        "navigate": "navigate",
        "play_media": "play_media",
    }

    REQUIRED_PARAMETERS = {
        "call_person": ("recipient",),
        "send_message": ("recipient", "request"),
        "open_app": ("app",),
        "create_reminder": ("request",),
        "navigate": ("location",),
        "play_media": ("request",),
    }

    def plan(self, intent: Intent) -> ActionPlan:
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent.")

        if intent.name == "unknown":
            raise ValueError("Cannot plan an unknown intent.")

        if intent.name == "check_notifications":
            return ActionPlan(actions=[])

        action_name = self.INTENT_ACTION_MAPPING.get(intent.name)

        if action_name is None:
            raise ValueError(
                f"Unsupported intent: {intent.name}"
            )

        required_parameters = self.REQUIRED_PARAMETERS[action_name]

        for parameter in required_parameters:
            value = intent.parameters.get(parameter)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Missing or invalid required parameter: {parameter}."
                )

        return ActionPlan(
            actions=[
                PlannedAction(
                    name=action_name,
                    parameters=dict(intent.parameters),
                )
            ]
        )
