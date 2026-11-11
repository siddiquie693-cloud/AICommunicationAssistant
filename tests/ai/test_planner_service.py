from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.intent.types import Intent
from ai.planner.service import ActionPlanner
from ai.planner.types import ActionPlan, PlannedAction
from ai.planner.service import IntentActionPlanner

class ActionPlannerTests(SimpleTestCase):

    def test_action_planner_delegates_planning_to_planner(self):
        planner = Mock()

        expected_plan = ActionPlan(
            actions=[
                PlannedAction(
                    name="call_person",
                    parameters={"recipient": "John"},
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
            name="call_person",
            parameters={"recipient": "John"},
        )

        with self.assertRaises(TypeError):
            engine.plan(intent)

class IntentActionPlannerTests(SimpleTestCase):

    def setUp(self):
        self.planner = IntentActionPlanner()

    def test_maps_call_person_intent(self):
        intent = Intent(
            name="call_person",
            parameters={"recipient": "John"},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].name, "call_person")
        self.assertEqual(
            plan.actions[0].parameters,
            {"recipient": "John"},
        )

    def test_maps_send_message_intent_with_recipient(self):
        intent = Intent(
            name="send_message",
            parameters={
                "recipient": "John",
                "request": "Hello John",
            },
        )

        plan = self.planner.plan(intent)

        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].name, "send_message")
        self.assertEqual(
            plan.actions[0].parameters,
            {
                "recipient": "John",
                "request": "Hello John",
            },
        )

    def test_rejects_message_without_recipient(self):
        intent = Intent(
            name="send_message",
            parameters={"request": "Hello John"},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_maps_open_app_intent(self):
        intent = Intent(
            name="open_app",
            parameters={"app": "calculator"},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(plan.actions[0].name, "open_app")

    def test_maps_create_reminder_intent(self):
        intent = Intent(
            name="create_reminder",
            parameters={"request": "Buy milk"},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(plan.actions[0].name, "create_reminder")

    def test_maps_navigation_intent(self):
        intent = Intent(
            name="navigate",
            parameters={"location": "Bhopal"},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(plan.actions[0].name, "navigate")

    def test_maps_play_media_intent(self):
        intent = Intent(
            name="play_media",
            parameters={"request": "Play music"},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(plan.actions[0].name, "play_media")

    def test_defers_notification_intent(self):
        intent = Intent(
            name="check_notifications",
            parameters={},
        )

        plan = self.planner.plan(intent)

        self.assertEqual(plan.actions, [])

    def test_rejects_unknown_intent(self):
        intent = Intent(
            name="unknown",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_unsupported_intent(self):
        intent = Intent(
            name="unsupported_action",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_call_without_recipient(self):
        intent = Intent(
            name="call_person",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_message_without_content(self):
        intent = Intent(
            name="send_message",
            parameters={"recipient": "John"},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_open_app_without_app_name(self):
        intent = Intent(
            name="open_app",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_reminder_without_details(self):
        intent = Intent(
            name="create_reminder",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_navigation_without_destination(self):
        intent = Intent(
            name="navigate",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)

    def test_rejects_media_without_request(self):
        intent = Intent(
            name="play_media",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.planner.plan(intent)
