from django.test import SimpleTestCase

from ai.retrieval.mock import MockRetriever
from ai.retrieval.types import RetrievalResult

class MockRetrieverTests(SimpleTestCase):
    def test_retrieve_returns_documents(self):
        retriever = MockRetriever(
            documents=[
                "Python is a programming language.",
                "Django is a Python web framework.",
            ]
        )

        results = retriever.retrieve("Python")

        self.assertEqual(
            results,
            [
                RetrievalResult(
                    content="Python is a programming language.",
                    score=1.0,
                ),
                RetrievalResult(
                    content="Django is a Python web framework.",
                    score=1.0,
                ),
            ],
        )

    def test_retrieve_respects_top_k(self):
        retriever = MockRetriever(
            documents=[
                "Document 1",
                "Document 2",
                "Document 3",
            ]
        )    

        results = retriever.retrieve(
            "document",
            top_k=2,
        )

        self.assertEqual(
            results,
            [
                RetrievalResult(
                    content="Document 1",
                    score=1.0,
                ),
                RetrievalResult(
                    content="Document 2",
                    score=1.0,
                ),
            ],
        )

    def test_empty_query_raises_error(self):
        retriever = MockRetriever()

        with self.assertRaises(ValueError):
            retriever.retrieve("  ")

    def test_invalid_top_k_raises_error(self):
        retriever = MockRetriever()

        with self.assertRaises(ValueError):
            retriever.retrieve(
                "Python",
                top_k=0,
            )            