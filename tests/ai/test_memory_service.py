from unittest.mock import Mock

from django.test import TestCase

from ai.memory.service import MemoryEngine
from ai.memory.types import MemoryQuery, MemoryResult


class MemoryEngineTests(TestCase):

    def test_memory_engine_delegates_retrieval_to_retriever(self):
        retriever = Mock()

        expected_results = [
            MemoryResult(
                content="John prefers email.",
                metadata={"source": "conversation"},
            ),
        ]

        retriever.retrieve.return_value = expected_results

        engine = MemoryEngine(retriever)

        query = MemoryQuery(
            text="What does John prefer?",
            user_id=2,
        )

        result = engine.retrieve(query)

        self.assertEqual(result, expected_results)
        retriever.retrieve.assert_called_once_with(query)

    def test_memory_engine_rejects_non_memory_query(self):
        retriever = Mock()
        engine = MemoryEngine(retriever)

        with self.assertRaises(TypeError):
            engine.retrieve("What does John prefer?")

    def test_memory_engine_rejects_invalid_retriever_result(self):
        retriever = Mock()
        retriever.retrieve.return_value = [
            "John prefers email.",
        ]

        engine = MemoryEngine(retriever)

        query = MemoryQuery(
            text="What does John prefer?",
            user_id=2,
        )

        with self.assertRaises(TypeError):
            engine.retrieve(query)

    def test_memory_engine_rejects_non_list_retriever_result(self):
        retriever = Mock()
        retriever.retrieve.return_value = MemoryResult(
            content="John prefers email.",
            metadata={},
        )

        engine = MemoryEngine(retriever)

        query = MemoryQuery(
            text="What does John prefer?",
            user_id=2,
        )

        with self.assertRaises(TypeError):
            engine.retrieve(query)

    def test_memory_engine_works_with_django_memory_retriever(self):
        from django.contrib.auth import get_user_model
        from django.test import TestCase

        from ai.memory.types import MemoryQuery
        from memory.models import Memory
        from memory.retriever import DjangoMemoryRetriever

        user = get_user_model().objects.create_user(
            username="memoryengineintegration",
            email="memoryengineintegration@example.com",
            password="testpass123",
        )

        Memory.objects.create(
            user=user,
            content="User prefers concise answers.",
            memory_type=Memory.MemoryType.PREFERENCE,
            importance=5,
        )

        engine = MemoryEngine(DjangoMemoryRetriever())

        results = engine.retrieve(
            MemoryQuery(
                text="response preferences",
                user_id=user.id,
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].content,
            "User prefers concise answers.",
        )        