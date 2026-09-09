from django.test import SimpleTestCase

from knowledge.services.vector_store.base import BaseVectorStore
from knowledge.services.vector_store.mock import MockVectorStore

class BaseVectorStoreTests(SimpleTestCase):

    def test_base_vector_store_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseVectorStore()

class MockVectorStoreTests(SimpleTestCase):

    def setUp(self):
        self.store = MockVectorStore()

    def test_add_and_search(self):
        self.store.add([1.0, 0.0], "Python")
        self.store.add([0.0, 1.0], "Django")

        results = self.store.search([1.0, 0.0])

        self.assertEqual(results[0][0], "Python")
        self.assertAlmostEqual(results[0][1], 1.0)

    def test_search_respects_top_k(self):
        self.store.add([1.0, 0.0], "Python")
        self.store.add([0.0, 1.0], "Django")
        self.store.add([1.0, 1.0], "FastAPI")

        results = self.store.search(
            [1.0, 0.0],
            top_k=2,
        )        

        self.assertEqual(len(results), 2)

    def test_empty_vector_raises_error(self):
        with self.assertRaises(ValueError):
            self.store.add([], "Python")

    def test_empty_content_raises_error(self):
        with self.assertRaises(ValueError):
            self.store.add([1.0, 0.0], "  ")

    def test_invalid_top_k_raises_error(self):
        with self.assertRaises(ValueError):
            self.store.search([1.0, 0.0], top_k=0)

    def test_mismatched_dimensions_raise_error(self):
        self.store.add([1.0, 0.0], "Python")

        with self.assertRaises(ValueError):
            self.store.search([1.0, 0.0, 0.0])                            