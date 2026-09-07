from django.test import SimpleTestCase

from ai.providers.mock import MockAIProvider

class MockAIProviderStreamingTests(SimpleTestCase):

    def test_generate_stream_returns_chunk(self):
        provider = MockAIProvider()

        chunks = list(
            provider.generate_stream("Hello AI")
        )

        self.assertGreater(len(chunks), 1)

        response = "".join(chunks)

        self.assertEqual(
            response,
            "Mock AI response: Hello AI",
        )

    def test_generate_stream_preserves_full_response(self):
        provider = MockAIProvider()

        chunks = list(
            provider.generate_stream(
                "This is a longer message for streaming."
            )
        )    

        response = "".join(chunks)

        self.assertEqual(
            response,
            provider.generate(
                "This is a longer message for streaming."
            ),
        )

    def test_generate_stream_with_messages(self):
        provider = MockAIProvider()

        messages = [
            {
                "role": "user",
                "content": "Hello",
            },
            {
                "role": "assistant",
                "content": "Hi there!",
            },
        ]    

        chunks = list(
            provider.generate_stream(
                "How are you?",
                messages=messages,
            )
        )

        response = "".join(chunks)

        self.assertIn("User: Hello", response)
        self.assertIn("Assistant: Hi there!", response)
        self.assertNotIn("User: How are you?", response)