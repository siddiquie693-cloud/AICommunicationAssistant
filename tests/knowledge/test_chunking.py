from django.test import SimpleTestCase

from knowledge.services.chunking import TextChunkingService

class TextChunkingServiceTests(SimpleTestCase):

    def test_chunk_splits_text(self):
        service = TextChunkingService(chunk_size=5)

        result = service.chunk("ABCDEFGHIJ")

        self.assertEqual(
            result,
            ["ABCDE", "FGHIJ"],
        )

    def test_chunk_hdles_remainder(self):
        service = TextChunkingService(chunk_size=4)

        result = service.chunk("ABCDEFGHI")

        self.assertEqual(
            result,
            ["ABCD", "EFGH", "I"],
        )    

    def test_empty__raises_error(self):
        service = TextChunkingService(chunk_size=5)

        with self.assertRaises(ValueError):
            service.chunk("  ")

    def test_invalid_chunk_size_raises_error(self):
        with self.assertRaises(ValueError):
            TextChunkingService(chunk_size=0)            