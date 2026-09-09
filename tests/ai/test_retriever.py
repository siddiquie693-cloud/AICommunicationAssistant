from unittest import TestCase

from ai.retrieval.base import BaseRetriever
from ai.retrieval.types import RetrievalResult

class BaseRetrieverTests(TestCase):
    def test_base_retriever_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseRetriever()

    def test_retrieve_is_abstract(self):
        self.assertTrue(
            getattr(
                BaseRetriever.retrieve,
                "__isabstractmethod__",
                False,
            )
        )

    def test_retrieval_result_contains_content_and_score(self):
        result = RetrievalResult(
            content="Python is a programming language.",
            score=0.95,
        )            

        self.assertEqual(
            result.content,
            "Python is a programming language.",
        )

        self.assertEqual(
            result.score,
            0.95,
        )