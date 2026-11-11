from django.test import SimpleTestCase

from ai.brain.types import BrainRequest
from ai.intent.detector import BasicIntentDetector, IntentDetector
from ai.intent.types import Intent
from ai.context.types import Context

class BasicIntentDetectorTests(SimpleTestCase):
    def setUp(self):
        self.detector = BasicIntentDetector()

    def test_basic_intent_detector_implements_intent_detector(self):
        self.assertIsInstance(
            self.detector,
            IntentDetector,
        )

    def test_basic_intent_detector_accepts_brain_request(self):
        request = BrainRequest(
            text="hello",
        )

        intent = self.detector.detect(request)

        self.assertIsInstance(intent, Intent)

    def test_basic_intent_detector_returns_unknown_intent(self):
        request = BrainRequest(
            text="hello",
        )

        intent = self.detector.detect(request)

        self.assertEqual(intent.name, "unknown")

    def test_basic_intent_detector_returns_empty_parameters_for_unknown_intent(self):
        request = BrainRequest(
            text="hello",
        )

        intent = self.detector.detect(request)

        self.assertEqual(intent.parameters, {})


    def test_basic_intent_detector_preserves_parameter_contract_across_intents(self):
        cases = (
            ("Call John", "call_person", {"recipient": "John"}),
            (
                "Send John a message",
                "send_message",
                {"request": "John a message"},
            ),
            ("Open WhatsApp", "open_app", {"app": "WhatsApp"}),
            (
                "Remind me to call John",
                "create_reminder",
                {"request": "Remind me to call John"},
            ),
            ("Navigate to the office", "navigate", {"location": "the office"}),
            (
                "Play music",
                "play_media",
                {"request": "Play music"},
            ),
            ("Check notifications", "check_notifications", {}),
        )

        detector = BasicIntentDetector()

        for text, expected_name, expected_parameters in cases:
            with self.subTest(text=text):
                intent = detector.detect(BrainRequest(text=text))

                self.assertEqual(intent.name, expected_name)
                self.assertEqual(intent.parameters, expected_parameters)

    def test_basic_intent_detector_preserves_parameter_contract_across_supported_intents(self):
        cases = (
            ("Call John", "call_person", {"recipient": "John"}),
            (
                "Send hello",
                "send_message",
                {"request": "hello"},
            ),
            ("Open WhatsApp", "open_app", {"app": "WhatsApp"}),
            (
                "Remind me to call John",
                "create_reminder",
                {"request": "Remind me to call John"},
            ),
            (
                "Navigate to the office",
                "navigate",
                {"location": "the office"},
            ),
            ("Play music", "play_media", {"request": "Play music"}),
            ("Check notifications", "check_notifications", {}),
        )

        for text, expected_name, expected_parameters in cases:
            with self.subTest(text=text):
                intent = self.detector.detect(BrainRequest(text=text))

                self.assertEqual(intent.name, expected_name)
                self.assertEqual(intent.parameters, expected_parameters)

    def test_basic_intent_detector_rejects_invalid_request(self):
        with self.assertRaises(TypeError):
            self.detector.detect("hello")

    def test_basic_intent_detector_detects_call_request(self):
        intent = self.detector.detect(
            BrainRequest(text="Call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )


    def test_basic_intent_detector_preserves_explicit_call_recipient(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Please call Sarah",
            ),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "Sarah"},
        )

    def test_basic_intent_detector_extracts_call_recipient_case_insensitively(self):
        intent = self.detector.detect(
            BrainRequest(
                text="CALL Sarah",
            ),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "Sarah"},
        )

    def test_basic_intent_detector_preserves_multiword_call_recipient(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Call John Smith",
            ),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John Smith"},
        )

    def test_basic_intent_detector_detects_message_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Send John a message",
            ),
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "John a message"},
        )


    def test_basic_intent_detector_extracts_explicit_message_recipient_and_content(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Send a message to John saying hello",
            ),
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "John",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_extracts_explicit_message_case_insensitively(self):
        intent = self.detector.detect(
            BrainRequest(
                text="SEND A MESSAGE TO John SAYING hello",
            ),
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "John",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_preserves_incomplete_explicit_message_request(self):
        for text in (
            "Send a message to John",
            "Send a message to John saying",
            "Send a message to saying hello",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "send_message")
                self.assertEqual(
                    intent.parameters,
                    {"request": text[len("Send "):]},
                )

    def test_basic_intent_detector_detects_open_app_request(self):
        intent = self.detector.detect(
            BrainRequest(text="Open WhatsApp"),
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "WhatsApp"},
        )

    def test_basic_intent_detector_preserves_multiword_app_name(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Open Google Maps",
            ),
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "Google Maps"},
        )

    def test_basic_intent_detector_extracts_app_name_case_insensitively(self):
        intent = self.detector.detect(
            BrainRequest(
                text="OPEN Google Maps",
            ),
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "Google Maps"},
        )

    def test_basic_intent_detector_preserves_multiword_app_name(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Open Google Maps",
            ),
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "Google Maps"},
        )

    def test_basic_intent_detector_detects_reminder_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Remind me to call John",
            ),
        )

        self.assertEqual(intent.name, "create_reminder")
        self.assertEqual(
            intent.parameters,
            {"request": "Remind me to call John"},
        )

    def test_basic_intent_detector_preserves_explicit_reminder_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Remind me to call John tomorrow",
            ),
        )

        self.assertEqual(intent.name, "create_reminder")
        self.assertEqual(
            intent.parameters,
            {"request": "Remind me to call John tomorrow"},
        )

    def test_basic_intent_detector_detects_navigation_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Go to Bhopal",
            ),
        )

        self.assertEqual(intent.name, "navigate")
        self.assertEqual(
            intent.parameters,
            {"location": "Bhopal"},
        )

    def test_basic_intent_detector_preserves_explicit_navigation_destination(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Navigate to the nearest hospital",
            ),
        )

        self.assertEqual(intent.name, "navigate")
        self.assertEqual(
            intent.parameters,
            {"location": "the nearest hospital"},
        )

    def test_basic_intent_detector_does_not_detect_navigation_without_destination(self):
        detector = BasicIntentDetector()

        for text in ("Navigate to", "Go to", "Take me to", "Directions to"):
            with self.subTest(text=text):
                intent = detector.detect(BrainRequest(text=text))

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_extracts_navigation_destination_case_insensitively(self):
        intent = self.detector.detect(
            BrainRequest(
                text="NAVIGATE TO the nearest hospital",
            ),
        )

        self.assertEqual(intent.name, "navigate")
        self.assertEqual(
            intent.parameters,
            {"location": "the nearest hospital"},
        )

    def test_basic_intent_detector_detects_media_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Play music",
            ),
        )

        self.assertEqual(intent.name, "play_media")
        self.assertEqual(
            intent.parameters,
            {"request": "Play music"},
        )

    def test_basic_intent_detector_preserves_multiword_media_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Play relaxing instrumental music",
            ),
        )

        self.assertEqual(intent.name, "play_media")
        self.assertEqual(
            intent.parameters,
            {"request": "Play relaxing instrumental music"},
        )

    def test_basic_intent_detector_preserves_media_request_case_insensitively(self):
        intent = self.detector.detect(
            BrainRequest(
                text="PLAY music",
            ),
        )

        self.assertEqual(intent.name, "play_media")
        self.assertEqual(
            intent.parameters,
            {"request": "PLAY music"},
        )

    def test_basic_intent_detector_detects_notification_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Check my notifications",
            ),
        )

        self.assertEqual(intent.name, "check_notifications")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_returns_unknown_for_unsupported_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="What is the meaning of life?",
            ),
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_supports_multiple_call_phrasings(self):
        for text in (
            "Call John",
            "Phone John",
            "Ring John",
            "Dial John",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "call_person")
                self.assertEqual(
                    intent.parameters,
                    {"recipient": "John"},
                )

    def test_basic_intent_detector_supports_multiple_message_phrasings(self):
        for text in (
            "Send John a message",
            "Message John",
            "Text John",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "send_message")

    def test_basic_intent_detector_supports_multiple_app_phrasings(self):
        for text in (
            "Open WhatsApp",
            "Start WhatsApp",
            "Launch WhatsApp",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "open_app")
                self.assertEqual(
                    intent.parameters,
                    {"app": "WhatsApp"},
                )

    def test_basic_intent_detector_supports_multiple_navigation_phrasings(self):
        for text in (
            "Navigate Bhopal",
            "Go to Bhopal",
            "Take me to Bhopal",
            "Directions to Bhopal",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "navigate")
                self.assertEqual(
                    intent.parameters,
                    {"location": "Bhopal"},
                )

    def test_basic_intent_detector_supports_multiple_reminder_phrasings(self):
        for text in (
            "Remind me to call John",
            "Set a reminder to call John",
            "Create a reminder to call John",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "create_reminder")

    def test_basic_intent_detector_does_not_detect_reminder_without_details(self):
        detector = BasicIntentDetector()

        for text in ("Remind me", "Set a reminder", "Create a reminder"):
            with self.subTest(text=text):
                intent = detector.detect(BrainRequest(text=text))

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_supports_multiple_notification_phrasings(self):
        for text in (
            "Show notifications",
            "Check notifications",
            "Check my notifications",
            "Show my notifications",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(
                    intent.name,
                    "check_notifications",
                )
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_direct_command(self):
        intent = self.detector.detect(
            BrainRequest(text="Call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_polite_command(self):
        intent = self.detector.detect(
            BrainRequest(text="Please call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_question_form_action(self):
        intent = self.detector.detect(
            BrainRequest(text="Can you call John?"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John?"},
        )

    def test_basic_intent_detector_handles_polite_message_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Could you message John?",
            ),
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "John?"},
        )

    def test_basic_intent_detector_keeps_information_question_unknown(self):
        intent = self.detector.detect(
            BrainRequest(
                text="What is the capital of India?",
            ),
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_keeps_general_question_unknown(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Can you explain artificial intelligence?",
            ),
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_greeting_as_conversation(self):
        for text in (
            "Hello",
            "Hi",
            "Hey",
            "Hi NIRA",
            "Hello NIRA",
            "Hey NIRA",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_time_based_greetings(self):
        for text in (
            "Good morning",
            "Good afternoon",
            "Good evening",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_thanks_as_conversation(self):
        for text in (
            "Thanks",
            "Thank you",
            "Thanks NIRA",
            "Thank you NIRA",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_conversational_question(self):
        intent = self.detector.detect(
            BrainRequest(text="How are you?"),
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_preserves_action_after_polite_prefix(self):
        intent = self.detector.detect(
            BrainRequest(text="Please call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_unsupported_request(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Book me a flight to Mumbai",
            )
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_handles_unsupported_question(self):
        intent = self.detector.detect(
            BrainRequest(
                text="What is the weather today?",
            )
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_does_not_guess_unsupported_action(self):
        intent = self.detector.detect(
            BrainRequest(
                text="Order a pizza for me",
            )
        )

        self.assertEqual(intent.name, "unknown")
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_normalizes_call_intent_output(self):
        intent = self.detector.detect(
            BrainRequest(text="Call John"),
        )

        self.assertIsInstance(intent.name, str)
        self.assertEqual(intent.name, "call_person")
        self.assertIsInstance(intent.parameters, dict)
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_normalizes_message_intent_output(self):
        intent = self.detector.detect(
            BrainRequest(text="Send hello to John"),
        )

        self.assertIsInstance(intent.name, str)
        self.assertEqual(intent.name, "send_message")
        self.assertIsInstance(intent.parameters, dict)
        self.assertEqual(
            intent.parameters,
            {"request": "hello to John"},
        )

    def test_basic_intent_detector_normalizes_app_intent_output(self):
        intent = self.detector.detect(
            BrainRequest(text="Open WhatsApp"),
        )

        self.assertIsInstance(intent.name, str)
        self.assertEqual(intent.name, "open_app")
        self.assertIsInstance(intent.parameters, dict)
        self.assertEqual(
            intent.parameters,
            {"app": "WhatsApp"},
        )

    def test_basic_intent_detector_normalizes_unknown_intent_output(self):
        intent = self.detector.detect(
            BrainRequest(text="Do something unsupported"),
        )

        self.assertIsInstance(intent.name, str)
        self.assertEqual(intent.name, "unknown")
        self.assertIsInstance(intent.parameters, dict)
        self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_preserves_natural_language_parameters(self):
        intent = self.detector.detect(
            BrainRequest(text="Please call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertIsInstance(intent.parameters, dict)
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_case_insensitive_requests(self):
        for text, expected_name in (
            ("CALL JOHN", "call_person"),
            ("SEND HELLO", "send_message"),
            ("OPEN WHATSAPP", "open_app"),
            ("PLAY MUSIC", "play_media"),
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, expected_name)

    def test_basic_intent_detector_ignores_leading_and_trailing_whitespace(self):
        intent = self.detector.detect(
            BrainRequest(text="   Call John   "),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_polite_request_variations(self):
        for text in (
            "Can you call John",
            "Could you call John",
            "Please call John",
            "Would you call John",
            "Will you call John",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "call_person")
                self.assertEqual(
                    intent.parameters,
                    {"recipient": "John"},
                )

    def test_basic_intent_detector_handles_multiple_navigation_requests(self):
        for text in (
            "Navigate to Mumbai",
            "Go to Mumbai",
            "Take me to Mumbai",
            "Directions to Mumbai",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "navigate")
                self.assertEqual(
                    intent.parameters,
                    {"location": "Mumbai"},
                )

    def test_basic_intent_detector_handles_multiple_app_requests(self):
        for text in (
            "Open WhatsApp",
            "Start WhatsApp",
            "Launch WhatsApp",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "open_app")
                self.assertEqual(
                    intent.parameters,
                    {"app": "WhatsApp"},
                )

    def test_basic_intent_detector_handles_conversational_requests_without_parameters(self):
        for text in (
            "Hello",
            "Good morning",
            "Thanks",
            "How are you?",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_returns_unknown_for_unrecognized_natural_language(self):
        for text in (
            "Tell me something interesting",
            "Do something useful",
            "Make my day better",
        ):
            with self.subTest(text=text):
                intent = self.detector.detect(
                    BrainRequest(text=text),
                )

                self.assertEqual(intent.name, "unknown")
                self.assertEqual(intent.parameters, {})

    def test_basic_intent_detector_accepts_optional_context(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call John",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_preserves_detection_without_context(self):
        intent = self.detector.detect(
            BrainRequest(text="Call John"),
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_accepts_empty_context(self):
        context = Context()

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_accepts_person_context(self):
        context = Context(
            person={
                "id": 1,
                "name": "John",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_preserves_person_context_for_supported_request(self):
        context = Context(
            person={
                "id": 1,
                "name": "John",
                "relationship": "friend",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_handles_missing_person_context(self):
        context = Context(
            person=None,
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_accepts_memory_context(self):
        context = Context(
            memory=[
                {
                    "content": "John is my close friend.",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_preserves_memory_context_for_supported_request(self):
        context = Context(
            memory=[
                {
                    "content": "WhatsApp is my preferred messaging app.",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Open WhatsApp"),
            context=context,
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "WhatsApp"},
        )

    def test_basic_intent_detector_handles_empty_memory_context(self):
        context = Context(
            memory=[],
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_accepts_profile_context(self):
        context = Context(
            profile={
                "preferred_language": "English",
                "timezone": "Asia/Kolkata",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_preserves_profile_context_for_supported_request(self):
        context = Context(
            profile={
                "preferred_language": "English",
                "voice_language": "English",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Open WhatsApp"),
            context=context,
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "WhatsApp"},
        )

    def test_basic_intent_detector_handles_missing_profile_context(self):
        context = Context(
            profile=None,
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_preserves_profile_with_contextual_message(self):
        context = Context(
            profile={
                "preferred_language": "English",
                "timezone": "Asia/Kolkata",
            },
            person={"name": "Sarah"},
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_does_not_treat_profile_preferences_as_intent(self):
        context = Context(
            profile={
                "preferred_language": "Hindi",
                "voice_language": "Hindi",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Open WhatsApp"),
            context=context,
        )

        self.assertEqual(intent.name, "open_app")
        self.assertEqual(
            intent.parameters,
            {"app": "WhatsApp"},
        )

    def test_basic_intent_detector_preserves_explicit_request_with_profile(self):
        context = Context(
            profile={
                "preferred_language": "Hindi",
                "timezone": "Asia/Kolkata",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Call John"),
            context=context,
        )

        self.assertEqual(intent.name, "call_person")
        self.assertEqual(
            intent.parameters,
            {"recipient": "John"},
        )

    def test_basic_intent_detector_resolves_recipient_from_conversation_context(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call John",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Send him hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "John",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_resolves_recipient_from_latest_relevant_conversation_message(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call Sarah",
                },
                {
                    "role": "assistant",
                    "content": "Calling Sarah.",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_does_not_guess_context_dependent_recipient(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "What is the weather today?",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Send him hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "request": "him hello",
            },
        )

    def test_basic_intent_detector_preserves_explicit_recipient_over_context(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call John",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Send Sarah hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "request": "Sarah hello",
            },
        )

    def test_basic_intent_detector_resolves_recipient_from_person_context(self):
        context = Context(
            person={
                "id": 12,
                "name": "Sarah",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_resolves_person_context_without_conversation(self):
        context = Context(
            conversation=[],
            person={
                "id": 15,
                "name": "John",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Send him how are you"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "John",
                "request": "how are you",
            },
        )

    def test_basic_intent_detector_does_not_guess_when_person_context_has_no_name(self):
        context = Context(
            person={
                "id": 21,
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Send her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "request": "her hello",
            },
        )

    def test_basic_intent_detector_prefers_person_context_for_contextual_recipient(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call John",
                },
            ],
            person={
                "id": 12,
                "name": "Sarah",
            },
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_resolves_recipient_from_memory_context(self):
        context = Context(
            memory=[
                {
                    "content": "Sarah is the user's colleague.",
                    "person_name": "Sarah",
                    "relationship": "colleague",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_uses_relevant_memory_for_contextual_recipient(self):
        context = Context(
            memory=[
                {
                    "content": "John is the user's colleague.",
                    "person_name": "John",
                    "relationship": "colleague",
                },
                {
                    "content": "Sarah is the user's manager.",
                    "person_name": "Sarah",
                    "relationship": "manager",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message my manager hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_does_not_guess_from_unrelated_memory(self):
        context = Context(
            memory=[
                {
                    "content": "The user prefers dark mode.",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Send her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "request": "her hello",
            },
        )

    def test_basic_intent_detector_does_not_guess_from_ambiguous_memory_context(self):
        context = Context(
            memory=[
                {
                    "content": "Sarah is the user's colleague.",
                    "person_name": "Sarah",
                    "relationship": "colleague",
                },
                {
                    "content": "Emily is the user's friend.",
                    "person_name": "Emily",
                    "relationship": "friend",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "her hello"},
        )


    def test_basic_intent_detector_does_not_guess_when_person_and_memory_context_conflict(self):
        context = Context(
            person={
                "id": 12,
                "name": "Sarah",
            },
            memory=[
                {
                    "content": "Emily is the user's friend.",
                    "person_name": "Emily",
                    "relationship": "friend",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "her hello"},
        )

    def test_basic_intent_detector_does_not_guess_when_multiple_people_match_relationship(self):
        context = Context(
            memory=[
                {
                    "content": "Sarah is the user's colleague.",
                    "person_name": "Sarah",
                    "relationship": "colleague",
                },
                {
                    "content": "John is the user's colleague.",
                    "person_name": "John",
                    "relationship": "colleague",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message my colleague hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "my colleague hello"},
        )

    def test_basic_intent_detector_preserves_explicit_recipient_despite_ambiguous_memory(self):
        context = Context(
            memory=[
                {
                    "content": "Sarah is the user's colleague.",
                    "person_name": "Sarah",
                    "relationship": "colleague",
                },
                {
                    "content": "Emily is the user's friend.",
                    "person_name": "Emily",
                    "relationship": "friend",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Send a message to John saying hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "John",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_prefers_person_context_over_memory_context(self):
        context = Context(
            person={
                "id": 12,
                "name": "Sarah",
            },
            memory=[
                {
                    "content": "John is the user's colleague.",
                    "person_name": "John",
                    "relationship": "colleague",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {
                "recipient": "Sarah",
                "request": "hello",
            },
        )

    def test_basic_intent_detector_does_not_guess_from_conflicting_context(self):
        context = Context(
            conversation=[
                {
                    "role": "user",
                    "content": "Call John",
                },
            ],
            memory=[
                {
                    "content": "Sarah is the user's colleague.",
                    "person_name": "Sarah",
                    "relationship": "colleague",
                },
            ],
        )

        intent = self.detector.detect(
            BrainRequest(text="Message her hello"),
            context=context,
        )

        self.assertEqual(intent.name, "send_message")
        self.assertEqual(
            intent.parameters,
            {"request": "her hello"},
        )
