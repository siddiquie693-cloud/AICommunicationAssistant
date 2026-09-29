from django.test import SimpleTestCase

from ai.context.types import Context


class ContextTests(SimpleTestCase):

    def test_context_stores_all_context_sources(self):
        context = Context(
            conversation=[
                {"role": "user", "content": "Hello"},
            ],
            memory=[
                {"fact": "User likes Python"},
            ],
            person={
                "name": "John",
            },
            knowledge="Company policy",
            profile={
                "preferred_language": "en",
            },
        )

        self.assertEqual(
            context.conversation,
            [{"role": "user", "content": "Hello"}],
        )
        self.assertEqual(
            context.memory,
            [{"fact": "User likes Python"}],
        )
        self.assertEqual(
            context.person,
            {"name": "John"},
        )
        self.assertEqual(
            context.knowledge,
            "Company policy",
        )
        self.assertEqual(
            context.profile,
            {"preferred_language": "en"},
        )

    def test_context_defaults_to_empty_sources(self):
        context = Context()

        self.assertEqual(context.conversation, [])
        self.assertEqual(context.memory, [])
        self.assertIsNone(context.person)
        self.assertEqual(context.knowledge, "")
        self.assertIsNone(context.profile)