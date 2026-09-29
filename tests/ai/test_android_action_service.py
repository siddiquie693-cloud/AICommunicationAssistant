from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.android.service import AndroidActionEngine
from ai.android.types import (
    AndroidActionRequest,
    AndroidActionResult,
)


class AndroidActionEngineTests(SimpleTestCase):

    def test_android_action_engine_delegates_execution_to_executor(self):
        executor = Mock()

        expected_result = AndroidActionResult(
            success=True,
            action_name="open_app",
            message="Calculator opened.",
        )

        executor.execute.return_value = expected_result

        engine = AndroidActionEngine(executor)

        request = AndroidActionRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
        )

        result = engine.execute(request)

        self.assertEqual(result, expected_result)
        executor.execute.assert_called_once_with(request)

    def test_android_action_engine_rejects_non_android_action_request(self):
        executor = Mock()
        engine = AndroidActionEngine(executor)

        with self.assertRaises(TypeError):
            engine.execute("open calculator")

    def test_android_action_engine_rejects_invalid_executor_result(self):
        executor = Mock()
        executor.execute.return_value = "Calculator opened."

        engine = AndroidActionEngine(executor)

        request = AndroidActionRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
        )

        with self.assertRaises(TypeError):
            engine.execute(request)