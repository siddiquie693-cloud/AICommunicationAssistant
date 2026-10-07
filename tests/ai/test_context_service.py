from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import Mock
from ai.brain.types import BrainRequest
from ai.context.builder import MemoryContextBuilder
from ai.context.service import ContextEngine
from ai.context.types import Context
from ai.memory.service import MemoryEngine
from memory.models import Memory
from people.models import Person

from memory.retriever import DjangoMemoryRetriever


class ContextEngineTests(TestCase):

    def test_context_engine_delegates_building_to_builder(self):
        from unittest.mock import Mock

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
        builder.build.assert_called_once_with(
            request,
            person=None,
            conversation=None,
        )

    def test_context_engine_rejects_non_brain_request(self):
        from unittest.mock import Mock

        builder = Mock()
        engine = ContextEngine(builder)

        with self.assertRaises(TypeError):
            engine.build("What is the company policy?")

    def test_context_engine_rejects_invalid_builder_result(self):
        from unittest.mock import Mock

        builder = Mock()
        builder.build.return_value = "invalid context"

        engine = ContextEngine(builder)

        request = BrainRequest(
            text="What is the company policy?",
        )

        with self.assertRaises(TypeError):
            engine.build(request)

    def test_context_engine_builds_memory_context_with_real_memory_engine(self):
        user = get_user_model().objects.create_user(
            username="contextengineintegration",
            email="contextengineintegration@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(
            DjangoMemoryRetriever()
        )

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        engine = ContextEngine(builder)

        request = BrainRequest(
            text="What kind of responses does the user prefer?",
        )

        context = engine.build(request)

        self.assertIsInstance(context, Context)
        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )

    def test_context_engine_includes_resolved_person_context(self):
        
        user = get_user_model().objects.create_user(
            username="contextengineperson",
            email="contextengineperson@example.com",
            password="testpass123",
        )

        person = Person.objects.create(
            user=user,
            name="Rahul Sharma",
            relationship=Person.RelationshipType.FRIEND,
        )

        memory_engine = Mock()
        memory_engine.retrieve.return_value = []

        person_context_service = Mock()
        person_context_service.build.return_value = {
            "id": person.id,
            "name": "Rahul Sharma",
            "relationship": Person.RelationshipType.FRIEND,
            "memories": [],
        }

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user=user,
            person_context_service=person_context_service,
        )

        engine = ContextEngine(builder)

        request = BrainRequest(
            text="Tell me about Rahul.",
        )

        context = engine.build(
            request,
            person=person,
        )

        self.assertIsInstance(context, Context)
        self.assertEqual(
            context.person,
            {
                "id": person.id,
                "name": "Rahul Sharma",
                "relationship": Person.RelationshipType.FRIEND,
                "memories": [],
            },
        )

        person_context_service.build.assert_called_once_with(
            user=user,
            person=person,
        )    