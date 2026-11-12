
from django.test import SimpleTestCase

from ai.planner.types import ActionPlan, PlannedAction
from ai.planner.execution import ActionExecutionOrder


class ActionExecutionOrderTests(SimpleTestCase):

    def setUp(self):
        self.executor = ActionExecutionOrder()

    def test_returns_actions_in_dependency_order(self):
        plan = ActionPlan(actions=[
            PlannedAction(name="open_app", action_id="action_1"),
            PlannedAction(
                name="send_message",
                action_id="action_2",
                depends_on=("action_1",),
            ),
        ])

        result = self.executor.get_order(plan)

        self.assertEqual(result, ("action_1", "action_2"))

    def test_rejects_unsatisfied_dependency(self):
        plan = ActionPlan(actions=[
            PlannedAction(
                name="send_message",
                action_id="action_2",
                depends_on=("action_1",),
            ),
            PlannedAction(name="open_app", action_id="action_1"),
        ])

        with self.assertRaises(ValueError):
            self.executor.get_order(plan)

    def test_rejects_action_without_id(self):
        plan = ActionPlan(actions=[
            PlannedAction(name="open_app"),
        ])

        with self.assertRaises(ValueError):
            self.executor.get_order(plan)

    def test_rejects_invalid_plan_type(self):
        with self.assertRaises(TypeError):
            self.executor.get_order("invalid")
