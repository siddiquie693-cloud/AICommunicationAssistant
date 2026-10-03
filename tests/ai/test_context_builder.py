from unittest.mock import Mock
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from ai.brain.types import BrainRequest
from ai.context.builder import MemoryContextBuilder
from ai.context.types import Context
from ai.memory.types import MemoryQuery, MemoryResult


class MemoryContextBuilderTests(TestCase):

    def test_builder_returns_context_with_retrieved_memories(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = [
            MemoryResult(
                content="User prefers concise responses.",
                metadata={
                    "memory_type": "preference",
                    "importance": 5,
                },
            ),
            MemoryResult(
                content="User works with Python.",
                metadata={
                    "memory_type": "fact",
                    "importance": 4,
                },
            ),
        ]

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        request = BrainRequest(
            text="How should you respond to me?",
        )

        context = builder.build(request)

        self.assertIsInstance(context, Context)
        self.assertEqual(
            context.memory,
            [
                {
                    "content": "User prefers concise responses.",
                    "memory_type": "preference",
                    "importance": 5,
                },
                {
                    "content": "User works with Python.",
                    "memory_type": "fact",
                    "importance": 4,
                },
            ],
        )

    def test_builder_retrieves_real_active_memory_for_user(self):
        from django.contrib.auth import get_user_model
        from memory.models import Memory
        from memory.retriever import DjangoMemoryRetriever
        from ai.memory.service import MemoryEngine

        user = get_user_model().objects.create_user(
            username="contextbuilderintegration",
            email="contextbuilderintegration@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(len(context.memory), 1)
        self.assertEqual(
            context.memory[0]["content"],
            "User prefers concise technical responses.",
        )
        self.assertEqual(
            context.memory[0]["memory_type"],
            Memory.MemoryType.PREFERENCE,
        )

    def test_builder_does_not_retrieve_other_users_memory(self):
        from django.contrib.auth import get_user_model
        from memory.models import Memory
        from memory.retriever import DjangoMemoryRetriever
        from ai.memory.service import MemoryEngine

        user = get_user_model().objects.create_user(
            username="contextbuilderowner",
            email="contextbuilderowner@example.com",
            password="testpass123",
        )

        other_user = get_user_model().objects.create_user(
            username="contextbuilderother",
            email="contextbuilderother@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=other_user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(context.memory, [])

    def test_builder_does_not_retrieve_inactive_or_expired_memory(self):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        from memory.models import Memory
        from memory.retriever import DjangoMemoryRetriever
        from ai.memory.service import MemoryEngine

        user = get_user_model().objects.create_user(
            username="contextbuilderactive",
            email="contextbuilderactive@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise technical responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            is_active=False,
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise professional responses.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        memory_engine = MemoryEngine(DjangoMemoryRetriever())

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=user.id,
        )

        context = builder.build(
            BrainRequest(
                text="What kind of responses does the user prefer?",
            )
        )

        self.assertEqual(context.memory, [])    

    def test_builder_passes_request_text_and_user_id_to_memory_engine(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = []

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=42,
        )

        request = BrainRequest(
            text="What are my preferences?",
        )

        builder.build(request)

        memory_engine.retrieve.assert_called_once_with(
            MemoryQuery(
                text="What are my preferences?",
                user_id=42,
            )
        )

    def test_builder_preserves_memory_result_metadata(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = [
            MemoryResult(
                content="User prefers English.",
                metadata={
                    "memory_id": 12,
                    "memory_type": "preference",
                    "importance": 5,
                    "source": "explicit",
                },
            ),
        ]

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=9,
        )

        request = BrainRequest(
            text="What language do I prefer?",
        )

        context = builder.build(request)

        self.assertEqual(
            context.memory[0],
            {
                "content": "User prefers English.",
                "memory_id": 12,
                "memory_type": "preference",
                "importance": 5,
                "source": "explicit",
            },
        )

    def test_builder_rejects_non_brain_request(self):
        memory_engine = Mock()

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        with self.assertRaises(TypeError):
            builder.build("What are my preferences?")

        memory_engine.retrieve.assert_not_called()

    def test_builder_returns_empty_memory_when_memory_engine_returns_no_results(self):
        memory_engine = Mock()
        memory_engine.retrieve.return_value = []

        builder = MemoryContextBuilder(
            memory_engine=memory_engine,
            user_id=7,
        )

        request = BrainRequest(
            text="What do you remember about me?",
        )

        context = builder.build(request)

        self.assertEqual(context.memory, [])
        self.assertIsInstance(context, Context)