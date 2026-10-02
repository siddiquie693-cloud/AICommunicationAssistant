from django.test import SimpleTestCase

from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT

class ConversationPromptTests(SimpleTestCase):

    def test_conversation_system_prompt_exists(self):
        self.assertTrue(
            CONVERSATION_SYSTEM_PROMPT.strip()
        )

    def test_conversation_system_prompt_contains_expected_behavior(self):
        self.assertIn(
            "helpful AI communication assistant",
            CONVERSATION_SYSTEM_PROMPT,
        )    

        self.assertIn(
            "conversation history",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "lower-priority guidance",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "safety",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "privacy",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "authorization",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "permission",
            CONVERSATION_SYSTEM_PROMPT,
        )

        self.assertIn(
            "system constraints",
            CONVERSATION_SYSTEM_PROMPT,
        )