from conversations.models import Conversation, Message
from conversations.services.ai_conversation_service import (
    AIConversationService,
)


class VoiceConversationService:
    """
    Orchestrates the complete voice conversation pipeline.
    """

    def __init__(
        self,
        ai_conversation_service=None,
    ):
        if ai_conversation_service is None:
            ai_conversation_service = AIConversationService()

        self.ai_conversation_service = ai_conversation_service

    def transcribe_audio(
        self,
        audio,
        *,
        language=None,
    ):
        return self.ai_conversation_service.transcribe_audio(
            audio,
            language=language,
        )    

    def process_transcription(
        self,
        conversation,
        transcript,
        *,
        target_language=None,
    ):
        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("Transcript cannot be empty.")

        user_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content=transcript.strip(),
        )

        assistant_message = (
            self.ai_conversation_service.generate_response(
                conversation,
                user_message,
                target_language=target_language,
            )
        )

        return user_message, assistant_message

    def synthesize_speech(
        self,
        text,
        *,
        language=None,
        voice=None,
    ):
        return self.ai_conversation_service.synthesize_speech(
            text,
            language=language,
            voice=voice,
        )

    def process_voice(
        self,
        conversation,
        audio,
        *,
        input_language=None,
        target_language=None,
        voice=None,
    ):
        transcript = self.transcribe_audio(
            audio,
            language=input_language,
        )

        user_message, assistant_message = (
            self.process_transcription(
                conversation,
                transcript,
                target_language=target_language,
            )
        )

        audio_output = self.synthesize_speech(
            assistant_message.content,
            language=target_language,
            voice=voice,
        )

        return {
            "transcript": transcript,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "audio": audio_output,
        }