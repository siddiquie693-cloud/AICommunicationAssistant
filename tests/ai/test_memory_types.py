from django.test import SimpleTestCase

from ai.memory.types import MemoryQuery, MemoryResult


class MemoryQueryTests(SimpleTestCase):

    def test_memory_query_stores_text_user_id_and_limit(self):
        query = MemoryQuery(
            text="What does John prefer?",
            user_id=2,
            limit=10,
        )

        self.assertEqual(query.text, "What does John prefer?")
        self.assertEqual(query.user_id, 2)
        self.assertEqual(query.limit, 10)

    def test_memory_query_uses_default_limit(self):
        query = MemoryQuery(
            text="What does John prefer?",
            user_id=2,
        )

        self.assertEqual(query.limit, 5)


class MemoryResultTests(SimpleTestCase):

    def test_memory_result_stores_content_and_metadata(self):
        result = MemoryResult(
            content="John prefers email.",
            metadata={
                "importance": 0.8,
                "source": "conversation",
            },
        )

        self.assertEqual(result.content, "John prefers email.")
        self.assertEqual(
            result.metadata,
            {
                "importance": 0.8,
                "source": "conversation",
            },
        )