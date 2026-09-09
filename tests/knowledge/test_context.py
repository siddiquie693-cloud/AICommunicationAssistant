from django.test import SimpleTestCase

from knowledge.services.context import RAGContextBuilder


class RAGContextBuilderTests(SimpleTestCase):

    def setUp(self):
        self.builder = RAGContextBuilder()

    def test_build_combines_retrieved_content(self):
        results = [
            ("Python is a programming language.", 0.95),
            ("Django is a web framework.", 0.90),
        ]

        result = self.builder.build(results)

        self.assertEqual(
            result,
            "Python is a programming language.\n\n"
            "Django is a web framework.",
        )

    def test_build_ignores_scores(self):
        results = [
            ("First document", 0.99),
            ("Second document", 0.50),
        ]

        result = self.builder.build(results)

        self.assertNotIn("0.99", result)
        self.assertNotIn("0.50", result)

    def test_build_strips_content(self):
        results = [
            ("  Python  ", 0.95),
            ("  Django  ", 0.90),
        ]

        result = self.builder.build(results)

        self.assertEqual(
            result,
            "Python\n\nDjango",
        )

    def test_build_empty_results_returns_empty_string(self):
        result = self.builder.build([])

        self.assertEqual(result, "")

    def test_build_ignores_empty_content(self):
        results = [
            ("First useful document", 0.95),
            ("", 0.90),
            ("  ", 0.85),
            ("Second useful document", 0.80),
        ]    

        context = RAGContextBuilder().build(results)

        self.assertEqual(
            context,
            "First useful document\n\nSecond useful document",
        )

    def test_build_preserves_result_order(self):
        results = [
            ("Most relevant document", 0.99),
            ("Second relevant document", 0.85),
            ("Third relevant document", 0.70),
        ]    

        context = RAGContextBuilder().build(results)

        self.assertEqual(
            context,
            "Most relevant document\n\n"
            "Second relevant document\n\n"
            "Third relevant document",
        )

    