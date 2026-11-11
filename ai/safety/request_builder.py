from ai.planner.types import PlannedAction
from ai.safety.types import SafetyLevel, SafetyRequest


class ActionSafetyRequestBuilder:
    """
    Builds safety requests from planned actions.
    """

    ACTION_RISK_MAPPING = {
        "open_app": SafetyLevel.LOW,
        "navigate": SafetyLevel.LOW,
        "play_media": SafetyLevel.LOW,
        "create_reminder": SafetyLevel.MEDIUM,
        "send_message": SafetyLevel.HIGH,
        "call_person": SafetyLevel.HIGH,
    }

    def build(self, action: PlannedAction) -> SafetyRequest:
        if not isinstance(action, PlannedAction):
            raise TypeError("action must be a PlannedAction.")

        risk_level = self.ACTION_RISK_MAPPING.get(action.name)

        if risk_level is None:
            raise ValueError(
                f"Unsupported action: {action.name}"
            )

        return SafetyRequest(
            action_name=action.name,
            parameters=dict(action.parameters),
            risk_level=risk_level,
        )