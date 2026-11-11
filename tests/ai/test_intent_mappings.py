from django.test import SimpleTestCase

from ai.intent.categories import IntentCategory
from ai.intent.mappings import (
    INTENT_CATEGORY_MAPPING,
    USER_REQUEST_INTENT_MAPPING,
)


class IntentMappingTests(SimpleTestCase):
    def test_user_request_mapping_contains_expected_intents(self):
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["call"],
            "call_person",
        )
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["message"],
            "send_message",
        )
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["open"],
            "open_app",
        )

    def test_user_request_mapping_contains_action_categories(self):
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["reminder"],
            "create_reminder",
        )
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["navigate"],
            "navigate",
        )
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["media"],
            "play_media",
        )

    def test_user_request_mapping_contains_notification_intent(self):
        self.assertEqual(
            USER_REQUEST_INTENT_MAPPING["notification"],
            "check_notifications",
        )

    def test_intent_category_mapping_contains_expected_categories(self):
        self.assertEqual(
            INTENT_CATEGORY_MAPPING["call_person"],
            IntentCategory.PHONE,
        )
        self.assertEqual(
            INTENT_CATEGORY_MAPPING["send_message"],
            IntentCategory.MESSAGING,
        )
        self.assertEqual(
            INTENT_CATEGORY_MAPPING["open_app"],
            IntentCategory.APP_CONTROL,
        )

    def test_intent_category_mapping_contains_all_supported_intents(self):
        expected_intents = {
            "call_person",
            "send_message",
            "open_app",
            "create_reminder",
            "navigate",
            "play_media",
            "check_notifications",
            "unknown",
        }

        self.assertEqual(
            set(INTENT_CATEGORY_MAPPING),
            expected_intents,
        )

    def test_unknown_intent_maps_to_unknown_category(self):
        self.assertEqual(
            INTENT_CATEGORY_MAPPING["unknown"],
            IntentCategory.UNKNOWN,
        )