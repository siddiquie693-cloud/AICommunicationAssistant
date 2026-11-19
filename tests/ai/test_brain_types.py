from django.test import SimpleTestCase

from ai.brain.types import ( 
    BrainPipelineResult,
    BrainRequest,
    PendingActionConfirmation,
)

class BrainRequestTests(SimpleTestCase):

    def test_brain_request_stores_text_source_and_language(self):
        request = BrainRequest(
            text="Call John",
            source="voice",
            language="en",
        )

        self.assertEqual(request.text, "Call John")
        self.assertEqual(request.source, "voice")
        self.assertEqual(request.language, "en")

    def test_brain_request_uses_text_as_default_source(self):
        request = BrainRequest(
            text="Hello",
        )

        self.assertEqual(request.source, "text")
        self.assertIsNone(request.language)

    def test_brain_request_rejects_non_string_text(self):
        with self.assertRaises(TypeError):
            BrainRequest(text=123)

    def test_brain_request_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            BrainRequest(text="")

    def test_brain_request_rejects_whitespace_only_text(self):
        with self.assertRaises(ValueError):
            BrainRequest(text="   ")

    def test_brain_request_rejects_invalid_source(self):
        with self.assertRaises(TypeError):
            BrainRequest(
                text="Hello",
                source=123,
            )

    def test_brain_request_rejects_empty_source(self):
        with self.assertRaises(ValueError):
            BrainRequest(
                text="Hello",
                source="",
            )

    def test_brain_request_rejects_invalid_language(self):
        with self.assertRaises(TypeError):
            BrainRequest(
                text="Hello",
                language=123,
            )   

class BrainPipelineResultTests(SimpleTestCase):

    def test_brain_pipeline_result_stores_pipeline_results(self):
        intent = object()
        context = object()
        action_plan = object()
        safety_results = [object()]
        action_results = [object()]

        result = BrainPipelineResult(
            intent=intent,
            context=context,
            action_plan=action_plan,
            safety_results=safety_results,
            action_results=action_results,
        )

        self.assertIs(result.intent, intent)
        self.assertIs(result.context, context)
        self.assertIs(result.action_plan, action_plan)
        self.assertIs(result.safety_results, safety_results)
        self.assertIs(result.action_results, action_results)

    def test_brain_pipeline_result_uses_empty_result_lists_by_default(self):
        result = BrainPipelineResult(
            intent=object(),
            context=object(),
            action_plan=object(),
            safety_results=[],
            action_results=[],
        )

        self.assertEqual(result.safety_results, [])
        self.assertEqual(result.action_results, [])

    def test_pending_confirmations_default_to_empty_list(self):
        result = BrainPipelineResult(
            intent=object(),
            context=object(),
            action_plan=object(),
            safety_results=[],
            action_results=[],
        )

        self.assertEqual(result.pending_confirmations, [])    

class PendingActionConfirmationTests(SimpleTestCase):

    def test_creates_valid_pending_confirmation(self):
        confirmation = PendingActionConfirmation(
            confirmation_id="confirm_001",
            action_name="send_message",
            parameters={
                "recipient": "John",
                "content": "Hello",
            },
            reason="User confirmation is required.",
        )

        self.assertEqual(
            confirmation.confirmation_id,
            "confirm_001",
        )
        self.assertEqual(
            confirmation.action_name,
            "send_message",
        )
        self.assertEqual(
            confirmation.parameters["recipient"],
            "John",
        )

    def test_rejects_empty_confirmation_id(self):
        with self.assertRaises(ValueError):
            PendingActionConfirmation(
                confirmation_id=" ",
                action_name="send_message",
                parameters={},
                reason="Approval required.",
            )

    def test_rejects_empty_action_name(self):
        with self.assertRaises(ValueError):
            PendingActionConfirmation(
                confirmation_id="confirm_001",
                action_name=" ",
                parameters={},
                reason="Approval required.",
            )

    def test_rejects_invalid_parameters(self):
        with self.assertRaises(TypeError):
            PendingActionConfirmation(
                confirmation_id="confirm_001",
                action_name="send_message",
                parameters="invalid",
                reason="Approval required.",
            )

    def test_rejects_invalid_reason(self):
        with self.assertRaises(TypeError):
            PendingActionConfirmation(
                confirmation_id="confirm_001",
                action_name="send_message",
                parameters={},
                reason=123,
            )