from django.test import SimpleTestCase

from ai.intent.types import Intent
from ai.intent.validator import IntentValidator


class IntentValidatorTests(SimpleTestCase):

    def setUp(self):
        self.validator = IntentValidator()

    def test_validator_accepts_supported_intent(self):
        intent = Intent(
            name="call_person",
            parameters={"recipient": "John"},
        )

        result = self.validator.validate(intent)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.intent, intent)
        self.assertEqual(result.errors, ())

    def test_validator_rejects_unknown_intent_name(self):
        intent = Intent(
            name="delete_everything",
            parameters={},
        )

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.errors,
            ("Unsupported intent name.",),
        )

    def test_validator_rejects_unknown_intent(self):
        intent = Intent(
            name="unknown",
            parameters={},
        )

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)

    def test_validator_rejects_non_intent_input(self):
        with self.assertRaises(TypeError):
            self.validator.validate("call John")

    def test_validator_rejects_call_without_recipient(self):
        intent = Intent(name="call_person", parameters={})

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("recipient", result.errors[0])

    def test_validator_rejects_message_without_content(self):
        intent = Intent(
            name="send_message",
            parameters={"request": "  "},
        )

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("request", result.errors[0])

    def test_validator_rejects_open_app_without_app_name(self):
        intent = Intent(name="open_app", parameters={})

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("app", result.errors[0])

    def test_validator_rejects_navigation_without_location(self):
        intent = Intent(name="navigate", parameters={})

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("location", result.errors[0])

    def test_validator_rejects_reminder_without_request(self):
        intent = Intent(name="create_reminder", parameters={})

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("request", result.errors[0])

    def test_validator_rejects_media_without_request(self):
        intent = Intent(name="play_media", parameters={})

        result = self.validator.validate(intent)

        self.assertFalse(result.is_valid)
        self.assertIn("request", result.errors[0])

    def test_validator_accepts_notification_without_parameters(self):
        intent = Intent(
            name="check_notifications",
            parameters={},
        )

        result = self.validator.validate(intent)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, ())
