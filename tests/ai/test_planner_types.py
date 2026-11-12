from django.test import SimpleTestCase

from ai.planner.types import ActionPlan, PlannedAction


class PlannedActionTests(SimpleTestCase):

    def test_planned_action_stores_name_and_parameters(self):
        action = PlannedAction(
            name="call_person",
            parameters={"recipient": "John"},
        )

        self.assertEqual(action.name, "call_person")
        self.assertEqual(
            action.parameters,
            {"recipient": "John"},
        )

    def test_planned_action_defaults_to_empty_parameters(self):
        action = PlannedAction(
            name="open_app",
        )

        self.assertEqual(action.parameters, {})

    def test_planned_action_stores_dependency_metadata(self):
        action = PlannedAction(
            name="send_message",
            action_id="action_2",
            depends_on=("action_1",),
            description="Send a message after resolving the contact.",
        )

        self.assertEqual(action.action_id, "action_2")
        self.assertEqual(action.depends_on, ("action_1",))
        self.assertEqual(
            action.description,
            "Send a message after resolving the contact.",
        )

class ActionPlanTests(SimpleTestCase):

    def test_action_plan_stores_ordered_actions(self):
        first_action = PlannedAction(
            name="call_contact",
            parameters={"recipient": "John", "request": "Hello John"},
        )
        second_action = PlannedAction(
            name="send_message",
            parameters={"recipient": "John"},
        )

        plan = ActionPlan(
            actions=[first_action, second_action],
        )

        self.assertEqual(
            plan.actions,
            [first_action, second_action],
        )

    def test_action_plan_defaults_to_empty_actions(self):
        plan = ActionPlan()

        self.assertEqual(plan.actions, [])

    def test_action_plan_stores_clarification_details(self):
        plan = ActionPlan(
            requires_clarification=True,
            clarification_question="Which contact should I message?",
        )

        self.assertTrue(plan.requires_clarification)
        self.assertEqual(
            plan.clarification_question,
            "Which contact should I message?",
        )

    def test_action_plan_stores_planning_errors(self):
        plan = ActionPlan(
            errors=("Missing recipient.",),
        )

        self.assertEqual(plan.errors, ("Missing recipient.",))
