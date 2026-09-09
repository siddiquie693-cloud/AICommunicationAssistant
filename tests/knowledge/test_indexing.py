from django.test import SimpleTestCase

from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.indexing import KnowledgeIndexingService
from knowledge.services.vector_store.mock import MockVectorStore


class KnowledgeIndexingServiceTests(SimpleTestCase):

    def setUp(self):
        self.embedding_service = MockEmbeddingService()
        self.vector_store = MockVectorStore()

        self.service = KnowledgeIndexingService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

    def test_index_chunks_stores_embeddings(self):
        chunks = [
            "Python",
            "Django",
        ]

        self.service.index_chunks(chunks)

        self.assertEqual(len(self.vector_store._items), 2)

        self.assertEqual(
            self.vector_store._items[0][1],
            "Python",
        )
        self.assertEqual(
            self.vector_store._items[1][1],
            "Django",
        )
        
    def test_index_chunks_strips_content(self):
        self.service.index_chunks(
            ["  Python is powerful.  "],
        )

        results = self.vector_store.search(
            self.embedding_service.embed(
                "Python is powerful.",
            ),
        )

        self.assertEqual(
            results[0][0],
            "Python is powerful.",
        )

    def test_empty_chunk_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.index_chunks(["   "])

    def test_multiple_chunks_are_indexed(self):
        chunks = [
            "Chunk one",
            "Chunk two",
            "Chunk three",
        ]

        self.service.index_chunks(chunks)

        self.assertEqual(
            len(self.vector_store._items),
            3,
        )