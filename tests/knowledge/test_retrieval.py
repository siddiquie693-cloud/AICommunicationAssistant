from django.test import SimpleTestCase
from unittest.mock import Mock
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

    def test_retrieve_preserves_similarity_scores(self):
        embedding_service = Mock()
        embedding_service.embed.return_value = [1.0, 2.0, 3.0]

        vector_store = Mock()
        vector_store.search.return_value = [
            ("Relevant document", 0.95),
            ("Another document", 0.80),
        ]

        service = KnowledgeRetrievalService(
            embedding_service=embedding_service,
            vector_store=vector_store,
        )

        results = service.retrieve(
            "test query",
            top_k=2,
        )

        self.assertEqual(
            results,
            [
                ("Relevant document", 0.95),
                ("Another document", 0.80),
            ],
        )

        vector_store.search.assert_called_once_with(
            [1.0, 2.0, 3.0],
            top_k=2,
        )        