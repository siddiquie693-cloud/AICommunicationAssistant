from django.test import SimpleTestCase

from ai.intent.categories import IntentCategory


class IntentCategoryTests(SimpleTestCase):
    def test_intent_category_contains_expected_categories(self):
        expected_categories = {
            "communication",
            "phone",
            "messaging",
            "app_control",
            "information",
            "navigation",
            "reminder",
            "notification",
            "media",
            "system",
            "unknown",
        }

        self.assertEqual(
            {category.value for category in IntentCategory},
            expected_categories,
        )

    def test_intent_category_values_are_strings(self):
        for category in IntentCategory:
            self.assertIsInstance(category.value, str)

    def test_unknown_intent_category_is_available(self):
        self.assertEqual(
            IntentCategory.UNKNOWN,
            "unknown",
        )