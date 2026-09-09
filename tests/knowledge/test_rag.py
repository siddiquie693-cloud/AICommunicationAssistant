from django.test import SimpleTestCase
from unittest.mock import Mock

from knowledge.services.rag import RAGService
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

    def test_build_context_retrieves_and_builds_context(self):
        self.retrieval_service = Mock()
        self.retrieval_service.retrieve.return_value = [
            ("First document", 0.95),
            ("Second document", 0.85),
        ]        

        context_builder = Mock()
        context_builder.build.return_value = (
            "First document\n\nSecond document"
        )

        service = RAGService(
            retrieval_service=self.retrieval_service,
            context_builder=context_builder,
        )

        context = service.build_context(
            "what is RAG?",
            top_k=2,
        )

        self.assertEqual(
            context,
            "First document\n\nSecond document",
        )

        self.retrieval_service.retrieve.assert_called_once_with(
            "what is RAG?",
            top_k=2,
        )

        context_builder.build.assert_called_once_with(
            [
                ("First document", 0.95),
                ("Second document", 0.85),
            ]
        )

    def test_build_context_forwards_top_k(self):
        retrieval_service = Mock()
        retrieval_service.retrieve.return_value = [
            ("Relevant document", 0.95),
        ]

        context_builder = Mock()
        context_builder.build.return_value = "Relevant document"

        service = RAGService(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
        )

        service.build_context(
            "test query",
            top_k=10,
        )

        retrieval_service.retrieve.assert_called_once_with(
            "test query",
            top_k=10,
        )  

    def test_build_context_returns_empty_string_when_no_results(self):
        retrieval_service = Mock()
        retrieval_service.retrieve.return_value = []

        context_builder = Mock()
        context_builder.build.return_value = ""

        service = RAGService(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
        )

        context = service.build_context("unknown query")

        self.assertEqual(context, "")

        retrieval_service.retrieve.assert_called_once_with(
            "unknown query",
            top_k=5,
        )

        context_builder.build.assert_called_once_with([]) 

    def test_build_context_passes_retrieved_results_to_context_builder(self):
        retrieval_service = Mock()
        retrieval_results = [
            ("Document A", 0.91),
            ("Document B", 0.82),
        ]
        retrieval_service.retrieve.return_value = retrieval_results

        context_builder = Mock()
        context_builder.build.return_value = "Document A\n\nDocument B"

        service = RAGService(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
        )

        result = service.build_context("test query", top_k=2)

        self.assertEqual(
            result,
            "Document A\n\nDocument B",
        )

        context_builder.build.assert_called_once_with(
            retrieval_results
        )    

    def test_build_context_propagates_retrieval_error(self):
        retrieval_service = Mock()
        retrieval_service.retrieve.side_effect = ValueError(
            "Query cannot be empty."
        )

        context_builder = Mock()

        service = RAGService(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
        )

        with self.assertRaises(ValueError):
            service.build_context("")
    
        context_builder.build.assert_not_called()    