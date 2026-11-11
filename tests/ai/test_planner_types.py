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