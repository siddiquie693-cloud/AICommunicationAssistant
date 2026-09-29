from unittest.mock import Mock

from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.context.service import ContextEngine
from ai.context.types import Context


class ContextEngineTests(SimpleTestCase):

    def test_context_engine_delegates_building_to_builder(self):
        builder = Mock()

        expected_context = Context(
            knowledge="Company policy",
        )

        builder.build.return_value = expected_context

        engine = ContextEngine(builder)

        request = BrainRequest(
            text="What is the company policy?",
            source="text",
            language="en",
        )

        result = engine.build(request)

        self.assertEqual(result, expected_context)
        builder.build.assert_called_once_with(request)

    def test_context_engine_rejects_non_brain_request(self):
        builder = Mock()
        engine = ContextEngine(builder)

        with self.assertRaises(TypeError):
            engine.build("What is the company policy?")

    def test_context_engine_rejects_invalid_builder_result(self):
        builder = Mock()
        builder.build.return_value = "invalid context"

        engine = ContextEngine(builder)

        request = BrainRequest(
            text="What is the company policy?",
        )

        with self.assertRaises(TypeError):
            engine.build(request)