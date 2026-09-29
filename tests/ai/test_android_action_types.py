from django.test import SimpleTestCase

from ai.android.types import (
    AndroidActionRequest,
    AndroidActionResult,
)


class AndroidActionRequestTests(SimpleTestCase):

    def test_android_action_request_stores_all_fields(self):
        request = AndroidActionRequest(
            action_name="open_app",
            parameters={"app": "calculator"},
        )

        self.assertEqual(
            request.action_name,
            "open_app",
        )
        self.assertEqual(
            request.parameters,
            {"app": "calculator"},
        )

    def test_android_action_request_defaults_to_empty_parameters(self):
        request = AndroidActionRequest(
            action_name="open_settings",
        )

        self.assertEqual(request.parameters, {})


class AndroidActionResultTests(SimpleTestCase):

    def test_android_action_result_stores_all_fields(self):
        result = AndroidActionResult(
            success=True,
            action_name="open_app",
            message="Calculator opened.",
            data={"package": "com.android.calculator2"},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.action_name, "open_app")
        self.assertEqual(result.message, "Calculator opened.")
        self.assertEqual(
            result.data,
            {"package": "com.android.calculator2"},
        )

    def test_android_action_result_defaults_to_empty_data(self):
        result = AndroidActionResult(
            success=False,
            action_name="open_app",
            message="Application not found.",
        )

        self.assertEqual(result.data, {})