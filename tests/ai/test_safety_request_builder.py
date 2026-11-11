from django.test import SimpleTestCase

from ai.planner.types import PlannedAction
from ai.safety.request_builder import ActionSafetyRequestBuilder
from ai.safety.types import SafetyLevel, SafetyRequest


class ActionSafetyRequestBuilderTests(SimpleTestCase):

    def setUp(self):
        self.builder = ActionSafetyRequestBuilder()

    def test_builds_low_risk_open_app_request(self):
        action = PlannedAction(
            name="open_app",
            parameters={"app": "calculator"},
        )

        result = self.builder.build(action)

        self.assertEqual(
            result,
            SafetyRequest(
                action_name="open_app",
                parameters={"app": "calculator"},
                risk_level=SafetyLevel.LOW,
            ),
        )

    def test_builds_low_risk_navigation_request(self):
        action = PlannedAction(
            name="navigate",
            parameters={"location": "Bhopal"},
        )

        result = self.builder.build(action)

        self.assertEqual(result.risk_level, SafetyLevel.LOW)

    def test_builds_low_risk_media_request(self):
        action = PlannedAction(
            name="play_media",
            parameters={"request": "Play music"},
        )

        result = self.builder.build(action)

        self.assertEqual(result.risk_level, SafetyLevel.LOW)

    def test_builds_medium_risk_reminder_request(self):
        action = PlannedAction(
            name="create_reminder",
            parameters={"request": "Buy milk"},
        )

        result = self.builder.build(action)

        self.assertEqual(result.risk_level, SafetyLevel.MEDIUM)

    def test_builds_high_risk_message_request(self):
        action = PlannedAction(
            name="send_message",
            parameters={
                "recipient": "John",
                "request": "Hello",
            },
        )

        result = self.builder.build(action)

        self.assertEqual(result.risk_level, SafetyLevel.HIGH)

    def test_builds_high_risk_call_request(self):
        action = PlannedAction(
            name="call_person",
            parameters={"recipient": "John"},
        )

        result = self.builder.build(action)

        self.assertEqual(result.risk_level, SafetyLevel.HIGH)

    def test_preserves_action_parameters(self):
        parameters = {"app": "calculator"}
        action = PlannedAction(
            name="open_app",
            parameters=parameters,
        )

        result = self.builder.build(action)

        self.assertEqual(result.parameters, parameters)

    def test_rejects_unsupported_action(self):
        action = PlannedAction(
            name="delete_all_data",
            parameters={},
        )

        with self.assertRaises(ValueError):
            self.builder.build(action)

    def test_rejects_non_planned_action(self):
        with self.assertRaises(TypeError):
            self.builder.build("open_app")