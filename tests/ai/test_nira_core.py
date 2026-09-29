from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.types import BrainPipelineResult, BrainRequest
from ai.core.service import NIRACore
from ai.brain.service import NIRABrain

class NIRACoreTests(SimpleTestCase):

    def test_nira_core_delegates_processing_to_brain(self):
        brain = Mock()

        expected_result = BrainPipelineResult(
            intent=Mock(),
            context=Mock(),
            action_plan=Mock(),
            safety_results=[],
            action_results=[],
        )

        brain.process.return_value = expected_result

        core = NIRACore(brain)

        request = BrainRequest(
            text="Open calculator",
        )

        result = core.process(request)

        self.assertEqual(result, expected_result)
        brain.process.assert_called_once_with(request)

    def test_nira_core_rejects_non_brain_request(self):
        brain = Mock()
        core = NIRACore(brain)

        with self.assertRaises(TypeError):
            core.process("Open calculator")

    def test_nira_core_rejects_invalid_brain_result(self):
        brain = Mock()
        brain.process.return_value = "invalid result"

        core = NIRACore(brain)

        request = BrainRequest(
            text="Open calculator",
        )

        with self.assertRaises(TypeError):
            core.process(request)   

    def test_nira_core_propagates_brain_exception(self):
        brain = Mock()
        brain.process.side_effect = RuntimeError(
            "Brain processing failed."
        )

        core = NIRACore(brain)

        request = BrainRequest(
            text="Open calculator",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Brain processing failed.",
        ):
            core.process(request)      

    def test_nira_core_rejects_missing_brain(self):
        with self.assertRaises(ValueError):
            NIRACore(None)         

    def test_nira_core_processes_request_through_real_brain(self):
        ai_service = Mock()

        intent_engine = Mock()
        context_engine = Mock()
        action_planner = Mock()
        safety_engine = Mock()
        android_action_engine = Mock()

        intent = Mock()
        context = Mock()
        action_plan = Mock()
        safety_result = Mock()
        action_result = Mock()

        request = BrainRequest(
            text="Open calculator",
        )

        safety_request = Mock()

        action = Mock()
        action.name = "open_app"
        action.parameters = {
            "app": "calculator",
            "_safety_request": safety_request,
        }

        action_plan.actions = [action]

        intent_engine.detect.return_value = intent
        context_engine.build.return_value = context
        action_planner.plan.return_value = action_plan
        safety_engine.evaluate.return_value = safety_result
        android_action_engine.execute.return_value = action_result

        safety_result.decision.value = "allow"

        brain = NIRABrain(
            ai_service,
            intent_engine=intent_engine,
            context_engine=context_engine,
            action_planner=action_planner,
            safety_engine=safety_engine,
            android_action_engine=android_action_engine,
        )

        core = NIRACore(brain)

        result = core.process(request)

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

    def test_nira_core_propagates_real_brain_exception(self):
        ai_service = Mock()

        intent_engine = Mock()
        context_engine = Mock()
        action_planner = Mock()
        safety_engine = Mock()
        android_action_engine = Mock()

        intent_engine.detect.side_effect = RuntimeError(
            "Intent detection failed."
        )

        brain = NIRABrain(
            ai_service,
            intent_engine=intent_engine,
            context_engine=context_engine,
            action_planner=action_planner,
            safety_engine=safety_engine,
            android_action_engine=android_action_engine,
        )

        core = NIRACore(brain)

        request = BrainRequest(
            text="Open calculator",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Intent detection failed.",
        ):
            core.process(request)               