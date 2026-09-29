from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.brain.types import BrainPipelineResult, BrainRequest

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
