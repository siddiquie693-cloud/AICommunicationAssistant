from django.test import SimpleTestCase

from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.retrieval import KnowledgeRetrievalService
from knowledge.services.vector_store.mock import MockVectorStore


class KnowledgeRetrievalServiceTests(SimpleTestCase):

    def setUp(self):
        self.embedding_service = MockEmbeddingService()
        self.vector_store = MockVectorStore()

        self.service = KnowledgeRetrievalService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

    def test_retrieve_returns_relevant_knowledge(self):
        chunks = [
            "Python",
            "Django",
        ]

        for chunk in chunks:
            vector = self.embedding_service.embed(chunk)
            self.vector_store.add(vector, chunk)

        results = self.service.retrieve(
            "Python",
            top_k=2,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], "Python")

    def test_retrieve_respects_top_k(self):
        chunks = [
            "Python",
            "Django",
            "Flask!",
        ]

        for chunk in chunks:
            vector = self.embedding_service.embed(chunk)
            self.vector_store.add(vector, chunk)

        results = self.service.retrieve(
            "Python",
            top_k=2,
        )

        self.assertEqual(len(results), 2)

    def test_empty_query_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.retrieve("   ")

    def test_invalid_top_k_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.retrieve("Python", top_k=0)