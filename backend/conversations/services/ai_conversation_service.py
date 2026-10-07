from ai.providers.factory import get_ai_provider
from ai.services.ai_service import AIService
from decouple import config
from django.conf import settings
from ai.context.conversation import ConversationContextBuilder

from ai.speech_to_text.factory import get_speech_to_text_service
from ai.speech_to_text.service import SpeechToTextService
from ai.text_to_speech.factory import get_text_to_speech_service
from ai.text_to_speech.service import TextToSpeechService
from ai.translation.factory import get_translation_service
from ai.translation.service import TranslationService
from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT

from conversations.models import Conversation, Message
from users.profile_services import get_or_create_nira_personal_profile
from knowledge.services.context import RAGContextBuilder
from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.rag import RAGService
from knowledge.services.retrieval import KnowledgeRetrievalService
from knowledge.services.vector_store.mock import MockVectorStore

from knowledge.services.profile_context import (
    NIRAPersonalProfileContextService,
)

class AIConversationService:
    """
    Application service responsible for generating AI responses
    within a conversation.
    """

    def __init__(
        self,
        provider_name=None,
        rag_service=None,
        embedding_service=None,
        vector_store=None,
        translation_service=None,
        speech_to_text_service=None,
        text_to_speech_service=None,
    ):
        provider = get_ai_provider(provider_name)
        self.ai_service = AIService(provider)

        if rag_service is None:
            if embedding_service is None:
                embedding_service = MockEmbeddingService()

            if vector_store is None:
                vector_store = MockVectorStore()

            rag_service = RAGService(
                retrieval_service=KnowledgeRetrievalService(
                    embedding_service=embedding_service,
                    vector_store=vector_store,
                ),
                context_builder=RAGContextBuilder(),
            )

        self.rag_service = rag_service

        self.profile_context_service = (
            NIRAPersonalProfileContextService()
        )

        if translation_service is None:
            translation_service = get_translation_service()

        self.translation_service = translation_service  

        if speech_to_text_service is None:
            speech_to_text_service = get_speech_to_text_service(
                settings.SPEECH_TO_TEXT_PROVIDER
            )

        self.speech_to_text_service = speech_to_text_service  

        if text_to_speech_service is None:
            text_to_speech_service = get_text_to_speech_service()
        self.text_to_speech_service = text_to_speech_service        

        self.memory_message_limit = config(
            "AI_MEMORY_MESSAGE_LIMIT",
            default=20,
            cast=int,
        )

        if self.memory_message_limit < 0:
            raise ValueError(
                "AI_MEMORY_MESSAGE_LIMIT cannot be negative."
            )

        self.conversation_context_builder = ConversationContextBuilder(
            message_limit=self.memory_message_limit,
        )

        if self.memory_message_limit < 0:
            raise ValueError(
                "AI_MEMORY_MESSAGE_LIMIT cannot be negative."
            )

    def _build_messages(
        self,
        conversation: Conversation,
        *,
        exclude_message_id: int | None = None,
    ) -> list[dict[str, str]]:
        return self.conversation_context_builder.build(
            conversation,
            exclude_message_id=exclude_message_id,
        )

    def _build_profile_context(
        self,
        conversation: Conversation,
        *,
        context_purpose: str = "general",
    ) -> str:
        profile, _ = get_or_create_nira_personal_profile(
            conversation.user,
        )

        return self.profile_context_service.build(
            profile,
            context_purpose=context_purpose,
        )

    def _build_ai_profile_context(
        self,
        conversation: Conversation,
        *,
        context_purpose: str = "general",
    ) -> str:
        return self._build_profile_context(
            conversation,
            context_purpose=context_purpose,
        )

    def _build_communication_style_instruction(
        self,
        conversation: Conversation,
    ) -> str:
        profile, _ = get_or_create_nira_personal_profile(
            conversation.user,
        )

        communication_style = profile.communication_style

        if not isinstance(communication_style, dict):
            return ""

        if not communication_style:
            return ""

        return (
            "Apply the user's communication preferences when "
            "generating the response. "
            f"Communication preferences: {communication_style}"
        )

    def _build_channel_preference_instruction(
        self,
        conversation: Conversation,
        *,
        channel: str | None = None,
    ) -> str:
        if not channel:
            return ""

        profile, _ = get_or_create_nira_personal_profile(
            conversation.user,
        )

        communication_style = profile.communication_style

        if not isinstance(communication_style, dict):
            return ""

        channels = communication_style.get("channels")

        if not isinstance(channels, dict):
            return ""

        channel_preferences = channels.get(channel)

        if not isinstance(channel_preferences, dict):
            return ""

        if not channel_preferences:
            return ""

        return (
            f"Apply the user's {channel} communication preferences "
            "when generating the response. "
            f"{channel.capitalize()} preferences: "
            f"{channel_preferences}"
        )

    def _build_preferred_language_instruction(
        self,
        conversation: Conversation,
    ) -> str:
        preferred_language = (
            conversation.user.preferred_language_ref
        )

        if not preferred_language:
            return ""

        language_name = preferred_language.name

        if not language_name:
            return ""

        return (
            "Respond in the user's preferred language. "
            f"The preferred language is: {language_name}."
        )
  
    def generate_response(
        self,
        conversation: Conversation,
        user_message: Message,
        *,
        rag_context: str | None = None,
        rag_top_k: int = 5,
        target_language: str | None = None,
        profile_context_purpose: str = "general",
        channel: str | None = None,
    ) -> Message:
        """
        Generate an AI response using the conversation history.
        """

        messages = self._build_messages(
            conversation,
            exclude_message_id=user_message.id,
        )

        if rag_context is None:
            rag_context = self.rag_service.build_context(
                user_message.content,
                top_k=rag_top_k,
            )

        profile_context = self._build_profile_context(
            conversation,
            context_purpose=profile_context_purpose,
        )    

        prompt = user_message.content

        context_parts = []

        communication_style = self._build_communication_style_instruction(
            conversation,
        )

        channel_preferences = self._build_channel_preference_instruction(
            conversation,
            channel=channel,
        )

        preferred_language = self._build_preferred_language_instruction(
            conversation,
        )

        if profile_context:
            context_parts.append(
                f"Personal profile context:\n{profile_context}"
            )

        if communication_style:
            context_parts.append(
                communication_style
            )    

        if channel_preferences:
            context_parts.append(
                channel_preferences
            )    

        if preferred_language:
            context_parts.append(
                preferred_language
            )    

        if rag_context:
            context_parts.append(
                f"Knowledge context:\n{rag_context}"
            )    

        context_text = "\n\n".join(context_parts)
        prompt = (
            "Use the following context to help answer the user.\n\n"
            f"{context_text}\n\n"
            f"User question:\n{user_message.content}"
        )    

        response_text = self.ai_service.generate_response(
            prompt,
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            messages=messages,
        )

        if target_language:
            response_text = self.translate_text(
                response_text,
                target_language=target_language,
            )

        if not response_text or not response_text.strip():
            raise ValueError("AI response cannot be empty.")

        return Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_ASSISTANT,
            content=response_text,
        )

    def translate_text(
        self,
        text: str,
        *,
        source_language: str | None = None,
        target_language: str,
    ) -> str:
        """
        Translate text using the configured translation service.
        """
        return self.translation_service.translate(
            text,
            source_language=source_language,
            target_language=target_language,
        )

    def transcribe_audio(
        self,
        audio,
        *,
        language: str | None = None,
    ) -> str:
        """
        Transcribe audio using the configured speech-to-text service.
        """
        return self.speech_to_text_service.transcribe(
            audio,
            language=language,
        )

    def synthesize_speech(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
    ):
        """
        Convert text to speech using the configured text-to-speech service.
        """
        return self.text_to_speech_service.synthesize(
            text,
            language=language,
            voice=voice,
        )

    def generate_stream(
        self,
        conversation: Conversation,
        user_message: Message,
        preferred_language: str | None = None,
    ):
        """
        Generate an AI response as a stream of text chunks
        and save the complete response as an assistant message.
        """

        messages = self._build_messages(
            conversation,
            exclude_message_id=user_message.id,
        )

        system_prompt = CONVERSATION_SYSTEM_PROMPT

        if preferred_language:
            system_prompt = (
                f"{CONVERSATION_SYSTEM_PROMPT}\n\n"
                f"Response in the user's preferred language. "
                f"The preferred language code is: "
                f"{preferred_language}."
            )

        chunks = self.ai_service.generate_stream(
            user_message.content,
            system_prompt=system_prompt,
            messages=messages,
        )

        collected_chunks = []

        for chunk in chunks:
            collected_chunks.append(chunk)
            yield chunk

        response_text = "".join(collected_chunks)

        if response_text.strip():
            Message.objects.create(
                conversation=conversation,
                sender_type=Message.SENDER_ASSISTANT,
                content=response_text,
            )