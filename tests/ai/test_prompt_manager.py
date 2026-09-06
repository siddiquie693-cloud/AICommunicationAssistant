from django.test import SimpleTestCase

from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
from ai.prompts.manager import PromptManager

class PromptManagerTests(SimpleTestCase):

    def test_get_conversation_system_prompt(self):
        prompt = PromptManager.get_conversation_system_prompt()

        self.assertEqual(
            prompt,
            CONVERSATION_SYSTEM_PROMPT,
        )

    def test_build_conversation_prompt_without_context(self):
        prompt = PromptManager.build_conversation_prompt("Hello")

        self.assertEqual(prompt, "Hello")

    def test_build_conversation_prompt_with_context(self):
        prompt = PromptManager.build_conversation_prompt(
            "How are you?",
            context="User previously asked about Python.",
        )

        self.assertIn(
            "Conversation context:",
            prompt,
        )
        self.assertIn(
            "User previously asked about Python.",
            prompt,
        )

        self.assertIn(
            "How are you?",
            prompt,
        )

    def test_build_conversation_prompt_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            PromptManager.build_conversation_prompt("")

    def test_build_conversation_prompt_strips_whitespace(self):
        prompt = PromptManager.build_conversation_prompt(" Hello ")

        self.assertEqual(prompt, "Hello")            

    def test_get_system_prompt_for_conversation(self):
        result = PromptManager.get_system_prompt("conversation")

        self.assertEqual(
            result,
            CONVERSATION_SYSTEM_PROMPT,
        )

    def test_unknown_prompt_type_raises_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unknown prompt type",
        ):
            PromptManager.get_system_prompt("unknown")  

    def test_system_prompts_contains_conversation_prompt(self):
        self.assertIn(
            "conversation",
            PromptManager.SYSTEM_PROMPTS,
        ) 

        self.assertEqual(
            PromptManager.SYSTEM_PROMPTS["conversation"],
            CONVERSATION_SYSTEM_PROMPT,
        )

    def test_system_prompt_type_is_case_insensitive(self):
        prompt = PromptManager.get_system_prompt(" CONVERSATION ")

        self.assertEqual(
            prompt,
            CONVERSATION_SYSTEM_PROMPT,
        )    

    def test_validate_system_prompts_succeeds(self):
        PromptManager.validate_system_prompts()

    def test_validate_system_prompts_rejects_empty_prompt(self):
        original_prompts = PromptManager.SYSTEM_PROMPTS.copy()

        try:
            PromptManager.SYSTEM_PROMPTS["test"] = " "        

            with self.assertRaisesRegex(
                ValueError,
                "System prompt 'test' cannot be empty",
            ):
                PromptManager.validate_system_prompts()
        finally:
            PromptManager.SYSTEM_PROMPTS = original_prompts

    def test_validate_system_prompt_rejects_non_string_prompt(self):
        original_prompts = PromptManager.SYSTEM_PROMPTS.copy()

        try:
            PromptManager.SYSTEM_PROMPTS["test"] = None

            with self.assertRaisesRegex(
                ValueError,
                "System prompt 'test' cannot be empty",
            ):
                PromptManager.validate_system_prompts()
        finally:
            PromptManager.SYSTEM_PROMPTS = original_prompts                        