from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.types import BrainPipelineResult, BrainRequest
from ai.core.service import NIRACore


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