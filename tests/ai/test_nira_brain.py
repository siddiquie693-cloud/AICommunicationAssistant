from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.service import NIRABrain
from ai.brain.types import BrainRequest
from ai.android.types import AndroidActionResult
from ai.context.types import Context
from ai.intent.types import Intent
from ai.planner.types import ActionPlan, PlannedAction
from ai.safety.types import (
    SafetyDecision,
    SafetyLevel,
    SafetyRequest,
    SafetyResult,
)

class NIRABrainTests(SimpleTestCase):

    def test_nira_brain_delegates_thinking_to_ai_service(self):
        ai_service = Mock()
        ai_service.generate_response.return_value = "Hello from NIRA."

        brain = NIRABrain(ai_service)

        request = BrainRequest(
            text="Hello",
            source="text",
            language="en",
        )

        result = brain.think(request)

        self.assertEqual(result, "Hello from NIRA.")
        ai_service.generate_response.assert_called_once_with(
            "Hello",
            system_prompt=None,
            messages=None,
        )

    def test_nira_brain_rejects_non_brain_request(self):
        ai_service = Mock()
        brain = NIRABrain(ai_service)

        with self.assertRaises(TypeError):
            brain.think("Hello")

    def test_nira_brain_processes_action_through_complete_pipeline(self):
        ai_service = Mock()

        intent_engine = Mock()
        context_engine = Mock()
        action_planner = Mock()
        safety_engine = Mock()
        android_action_engine = Mock()

        request = BrainRequest(
            text="Open calculator",
        )

        intent = Intent(
            name="open_app",
            parameters={"app": "calculator"},
        )

        context = Context(
            profile={"preferred_language": "en"},
        )

        safety_request = SafetyRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
            risk_level=SafetyLevel.LOW,
        )

        action = PlannedAction(
            name="open_app",
            parameters={
                "app": "calculator",
                "_safety_request": safety_request,
            },
        )

        action_plan = ActionPlan(
            actions=[action],
        )

        safety_result = SafetyResult(
            decision=SafetyDecision.ALLOW,
            reason="Action is safe.",
        )

        action_result = AndroidActionResult(
            success=True,
            action_name="open_app",
            message="Calculator opened.",
        )

        intent_engine.detect.return_value = intent
        context_engine.build.return_value = context
        action_planner.plan.return_value = action_plan
        safety_engine.evaluate.return_value = safety_result
        android_action_engine.execute.return_value = action_result

        brain = NIRABrain(
            ai_service,
            intent_engine=intent_engine,
            context_engine=context_engine,
            action_planner=action_planner,
            safety_engine=safety_engine,
            android_action_engine=android_action_engine,
        )

        result = brain.process(request)

        self.assertEqual(result.intent, intent)
        self.assertEqual(result.context, context)
        self.assertEqual(result.action_plan, action_plan)
        self.assertEqual(
            result.safety_results,
            [safety_result],
        )
        self.assertEqual(
            result.action_results,
            [action_result],
        )

        intent_engine.detect.assert_called_once_with(request)
        context_engine.build.assert_called_once_with(request)
        action_planner.plan.assert_called_once_with(intent)
        safety_engine.evaluate.assert_called_once_with(
            safety_request
        )

        android_action_engine.execute.assert_called_once()        

    def test_nira_brain_does_not_execute_action_when_safety_requires_confirmation(self):
        ai_service = Mock()

        intent_engine = Mock()
        context_engine = Mock()
        action_planner = Mock()
        safety_engine = Mock()
        android_action_engine = Mock()

        request = BrainRequest(
            text="Send a message to John",
        )

        intent = Intent(
            name="send_message",
            parameters={"recipient": "John"},
        )

        context = Context()

        safety_request = SafetyRequest(
            action_name="send_message",
            parameters={
                "recipient": "John",
                "content": "Hello",
            },
            risk_level=SafetyLevel.MEDIUM,
        )

        action = PlannedAction(
            name="send_message",
            parameters={
                "recipient": "John",
                "content": "Hello",
                "_safety_request": safety_request,
            },
        )

        action_plan = ActionPlan(
            actions=[action],
        )

        safety_result = SafetyResult(
            decision=SafetyDecision.CONFIRM,
            reason="User confirmation is required.",
        )

        intent_engine.detect.return_value = intent
        context_engine.build.return_value = context
        action_planner.plan.return_value = action_plan
        safety_engine.evaluate.return_value = safety_result

        brain = NIRABrain(
            ai_service,
            intent_engine=intent_engine,
            context_engine=context_engine,
            action_planner=action_planner,
            safety_engine=safety_engine,
            android_action_engine=android_action_engine,
        )

        result = brain.process(request)

        self.assertEqual(
            result.safety_results,
            [safety_result],
        )
        self.assertEqual(result.action_results, [])

        android_action_engine.execute.assert_not_called()    