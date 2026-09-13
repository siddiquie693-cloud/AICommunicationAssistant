from django.test import TestCase

from conversations.models import Conversation, Message
from conversations.services.voice_conversation_service import (
    VoiceConversationService,
)
from users.models import User


class VoiceConversationServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="voiceuser",
            email="voice@example.com",
            password="TestPassword123",
        )

        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Voice Conversation",
        )

    def test_transcribe_audio_delegates_to_ai_conversation_service(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                return "Hello from audio"

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )

        result = service.transcribe_audio(
            b"audio-data",
            language="en",
        )

        self.assertEqual(
            result,
            "Hello from audio",
        )

    def test_process_transcription_creates_user_message_and_generates_response(self):
        class FakeAIConversationService:
            def generate_response(
                self,
                conversation,
                user_message,
                *,
                target_language=None,
            ):
                return Message.objects.create(
                    conversation=conversation,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="AI voice response",
                )

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )

        user_message, assistant_message = (
            service.process_transcription(
                self.conversation,
                "  Hello from voice  ",
            )
        )

        self.assertEqual(
            user_message.content,
            "Hello from voice",
        )

        self.assertEqual(
            user_message.sender_type,
            Message.SENDER_USER,
        )

        self.assertEqual(
            assistant_message.content,
            "AI voice response",
        )

        self.assertEqual(
            assistant_message.sender_type,
            Message.SENDER_ASSISTANT,
        )

    def test_synthesize_speech_delegates_to_ai_conversation_service(self):
        class FakeAIConversationService:
            def synthesize_speech(
                self,
                text,
                *,
                language=None,
                voice=None,
            ):
                return b"voice-audio"

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )

        result = service.synthesize_speech(
            "Hello",
            language="en",
            voice="default",
        )

        self.assertEqual(
            result,
            b"voice-audio",
        )

    def test_process_voice_runs_complete_voice_pipeline(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                return "Hello from voice"

            def generate_response(
                self,
                conversation,
                user_message,
                *,
                target_language=None,
            ):
                return Message.objects.create(
                    conversation=conversation,
                    sender_type=Message.SENDER_ASSISTANT,
                    content="Hello from AI",
                )

            def synthesize_speech(
                self,
                text,
                *,
                language=None,
                voice=None,
            ):
                return b"final-audio"

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )

        result = service.process_voice(
            self.conversation,
            b"input-audio",
            input_language="en",
            target_language="en",
            voice="default",
        )

        self.assertEqual(
            result["transcript"],
            "Hello from voice",
        )

        self.assertEqual(
            result["user_message"].content,
            "Hello from voice",
        )

        self.assertEqual(
            result["assistant_message"].content,
            "Hello from AI",
        )

        self.assertEqual(
            result["audio"],
            b"final-audio",
        )    

    def test_process_transcription_rejects_empty_transcript(self):
        service = VoiceConversationService(
            ai_conversation_service=object(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Transcript cannot be empty.",
        ):
            service.process_transcription(
                self.conversation,
                "   ",
            )

    def test_process_transcription_rejects_non_string_transcript(self):
        service = VoiceConversationService(
            ai_conversation_service=object(),
        )

        with self.assertRaisesMessage(
            ValueError,
            "Transcript cannot be empty.",
        ):
            service.process_transcription(
                self.conversation,
                None,
            )    

    def test_process_voice_rejects_empty_transcript(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                return "  "
        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )            

        with self.assertRaisesMessage(
            ValueError,
            "Transcript cannot be empty.",
        ):
            service.process_voice(
                self.conversation,
                b"input-audio",
                input_language="en",
            )

    def test_process_voice_rejects_non_string_transcript(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                return None

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )            

        with self.assertRaisesMessage(
            ValueError,
            "Transcript cannot be empty.",
        ):
            service.process_voice(
                self.conversation,
                b"input-audio",
                input_language="en",
            )

    def test_process_voice_rejects_empty_audio(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                if audio is None:
                    raise ValueError("Audio cannot be empty.")
                return "Hello"

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )  

        with self.assertRaisesMessage(
            ValueError,
            "Audio cannot be empty.",
        ):
            service.process_voice(
                self.conversation,
                None,
                input_language="en",
            )      

    def test_process_voice_rejects_non_string_audio(self):
        class FakeAIConversationService:
            def transcribe_audio(
                self,
                audio,
                *,
                language=None,
            ):
                if not isinstance(audio, (bytes, bytearray)):
                    raise ValueError("Audio must be bytes.")
                return "Hello"

        service = VoiceConversationService(
            ai_conversation_service=FakeAIConversationService(),
        )            

        with self.assertRaisesMessage(
            ValueError,
            "Audio must be bytes.",
        ):
            service.process_voice(
                self.conversation,
                "invalid-audio",
                input_language="en",
            )