from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.intent.types import Intent
from ai.planner.service import ActionPlanner
from ai.planner.types import ActionPlan, PlannedAction


class ActionPlannerTests(SimpleTestCase):

    def test_action_planner_delegates_planning_to_planner(self):
        planner = Mock()

        expected_plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="call_contact",
                    parameters={"contact": "John"},
                ),
            ],
        )

        planner.plan.return_value = expected_plan

        engine = ActionPlanner(planner)

        intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )

        result = engine.plan(intent)

        self.assertEqual(result, expected_plan)
        planner.plan.assert_called_once_with(intent)

    def test_action_planner_rejects_non_intent(self):
        planner = Mock()
        engine = ActionPlanner(planner)

        with self.assertRaises(TypeError):
            engine.plan("Call John")

    def test_action_planner_rejects_invalid_planner_result(self):
        planner = Mock()
        planner.plan.return_value = "call_contact"

        engine = ActionPlanner(planner)

        intent = Intent(
            name="call_contact",
            parameters={"contact": "John"},
        )

        with self.assertRaises(TypeError):
            engine.plan(intent)