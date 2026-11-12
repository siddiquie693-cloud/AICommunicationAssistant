from ai.intent.types import Intent
from ai.planner.types import ActionPlan, PlannedAction
from dataclasses import replace
from ai.planner.validator import ActionPlanValidator

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

    def plan_with_clarification(self, intent: Intent) -> ActionPlan:
        """
        Create an action plan with structured clarification support.
        """
        if not isinstance(intent, Intent):
            raise TypeError("intent must be an Intent.")

        planner_method = getattr(
            type(self.planner),
            "plan_with_clarification",
            None,
        )

        if callable(planner_method):
            action_plan = self.planner.plan_with_clarification(intent)
        else:
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
            raise ValueError(f"Unsupported intent: {intent.name}")

        required_parameters = self.REQUIRED_PARAMETERS[action_name]
        missing_parameters = []

        for parameter in required_parameters:
            value = intent.parameters.get(parameter)

            if not isinstance(value, str) or not value.strip():
                missing_parameters.append(parameter)

        if missing_parameters:
            raise ValueError(
                "Missing or invalid required parameter(s): "
                + ", ".join(missing_parameters)
                + "."
            )

        return ActionPlan(
            actions=[
                PlannedAction(
                    name=action_name,
                    parameters=dict(intent.parameters),
                    action_id="action_1",
                    description=f"Execute the {action_name} action.",
                )
            ]
        )

    def plan_with_clarification(self, intent: Intent) -> ActionPlan:
        """
        Return a clarification request when required information is missing.
        """
        try:
            return self.plan(intent)

        except ValueError as error:
            message = str(error)
            prefix = "Missing or invalid required parameter(s): "

            if not message.startswith(prefix):
                raise

            missing_parameters = (
                message[len(prefix):]
                .removesuffix(".")
                .split(", ")
            )

            question = (
                "Please provide the following information: "
                + ", ".join(missing_parameters)
                + "."
            )

            return ActionPlan(
                requires_clarification=True,
                clarification_question=question,
                errors=(message,),
            )


class MultiStepActionPlanner:
    """
    Combines multiple validated intents into an ordered action plan.

    Each action depends on the preceding action.
    This planner creates plans only; it never authorizes or executes them.
    """

    def __init__(self, single_action_planner=None):
        self.single_action_planner = (
            single_action_planner or IntentActionPlanner()
        )
        self.validator = ActionPlanValidator()

    def _resolve_contextual_intent(self, intent, context):
        if context is None or not isinstance(context.person, dict):
            return intent

        parameters = dict(intent.parameters)
        recipient = parameters.get("recipient")

        pronouns = {"him", "her", "them", "that person"}

        if (
            isinstance(recipient, str)
            and recipient.strip().lower() in pronouns
        ):
            person_name = context.person.get("name")

            if isinstance(person_name, str) and person_name.strip():
                parameters["recipient"] = person_name

        return replace(intent, parameters=parameters)

    def plan(
        self,
        intents: list[Intent],
        *,
        context=None,
    ) -> ActionPlan:

        if not isinstance(intents, (list, tuple)):
            raise TypeError("intents must be a list or tuple.")

        if not intents:
            raise ValueError("At least one intent is required.")

        actions = []
        previous_action_id = None

        if context is not None:
            from ai.context.types import Context

            if not isinstance(context, Context):
                raise TypeError("context must be a Context.")

        for intent in intents:
            resolved_intent = self._resolve_contextual_intent(
                intent,
                context,
            )
            single_plan = self.single_action_planner.plan(resolved_intent)

            for action in single_plan.actions:
                action_id = f"action_{len(actions) + 1}"

                dependencies = (
                    (previous_action_id,)
                    if previous_action_id is not None
                    else ()
                )

                planned_action = replace(
                    action,
                    action_id=action_id,
                    depends_on=dependencies,
                )

                actions.append(planned_action)
                previous_action_id = action_id

        action_plan = ActionPlan(actions=actions)
        validation = self.validator.validate(action_plan)

        if not validation.is_valid:
            raise ValueError(
                "Invalid multi-step action plan: "
                + "; ".join(validation.errors)
            )

        return action_plan
