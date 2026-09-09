from django.test import SimpleTestCase

from knowledge.services.embeddings.base import BaseEmbeddingService
from knowledge.services.embeddings.mock import MockEmbeddingService

class BaseEmbeddingServiceTests(SimpleTestCase):

    def test_base_embedding_service_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseEmbeddingService()

class MockEmbeddingServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = MockEmbeddingService()

    def test_embed_returns_vector(self):
        result = self.service.embed("ABC")

        self.assertEqual(
            result,
            [65.0, 66.0, 67.0],
        )    

    def test_embed_strips_text(self):
        result = self.service.embed("  ABC  ")

        self.assertEqual(
            result,
            [65.0, 66.0, 67.0],
        )    

    def test_empty_text_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.embed("  ")    