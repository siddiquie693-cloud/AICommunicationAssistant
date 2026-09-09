from django.test import SimpleTestCase

from knowledge.services.context import RAGContextBuilder
from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.rag import RAGService
from knowledge.services.retrieval import KnowledgeRetrievalService
from knowledge.services.vector_store.mock import MockVectorStore


class RAGServiceTests(SimpleTestCase):

    def setUp(self):
        self.embedding_service = MockEmbeddingService()
        self.vector_store = MockVectorStore()

        self.retrieval_service = KnowledgeRetrievalService(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        self.context_builder = RAGContextBuilder()

        self.service = RAGService(
            retrieval_service=self.retrieval_service,
            context_builder=self.context_builder,
        )

    def test_build_context_returns_retrieved_knowledge(self):
        chunks = [
            "Python",
            "Django",
        ]

        for chunk in chunks:
            vector = self.embedding_service.embed(chunk)
            self.vector_store.add(vector, chunk)

        result = self.service.build_context(
            "Python",
            top_k=2,
        )

        self.assertIn("Python", result)
        self.assertIn("Django", result)

    def test_build_context_respects_top_k(self):
        chunks = [
            "Python",
            "Django",
            "Flask!",
        ]

        for chunk in chunks:
            vector = self.embedding_service.embed(chunk)
            self.vector_store.add(vector, chunk)

        result = self.service.build_context(
            "Python",
            top_k=2,
        )

        self.assertEqual(
            len(result.split("\n\n")),
            2,
        )

    def test_empty_query_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.build_context("   ")