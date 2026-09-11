from ai.providers.factory import get_ai_provider
from ai.services.ai_service import AIService
from decouple import config
from ai.speech_to_text.factory import get_speech_to_text_service
from ai.speech_to_text.service import SpeechToTextService

from ai.translation.factory import get_translation_service
from ai.translation.service import TranslationService
from ai.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
from conversations.models import Conversation, Message
from knowledge.services.context import RAGContextBuilder
from knowledge.services.embeddings.mock import MockEmbeddingService
from knowledge.services.rag import RAGService
from knowledge.services.retrieval import KnowledgeRetrievalService
from knowledge.services.vector_store.mock import MockVectorStore


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

        if translation_service is None:
            translation_service = get_translation_service()

        self.translation_service = translation_service  

        if speech_to_text_service is None:
            speech_to_text_service = get_speech_to_text_service()

        self.speech_to_text_service = speech_to_text_service      

        self.memory_message_limit = config(
            "AI_MEMORY_MESSAGE_LIMIT",
            default=20,
            cast=int,
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
        """
        Build structured AI messages from conversation history.
        """

        conversation_messages = conversation.messages.order_by(
            "-created_at",
            "-id",
        )

        if exclude_message_id is not None:
            conversation_messages = conversation_messages.exclude(
                id=exclude_message_id,
            )

        conversation_messages = list(
            conversation_messages[: self.memory_message_limit]
        )

        conversation_messages.reverse()

        messages = []

        for message in conversation_messages:
            role = (
                "user"
                if message.sender_type == Message.SENDER_USER
                else "assistant"
            )

            messages.append(
                {
                    "role": role,
                    "content": message.content,
                }
            )

        return messages

    def generate_response(
        self,
        conversation: Conversation,
        user_message: Message,
        *,
        rag_context: str | None = None,
        rag_top_k: int = 5,
        target_language: str | None = None,
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

        prompt = user_message.content

        if rag_context:
            prompt = (
                "Use the following knowledge context to help answer the user.\n\n"
                f"Knowledge context:\n{rag_context}\n\n"
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

    def generate_stream(
        self,
        conversation: Conversation,
        user_message: Message,
    ):
        """
        Generate an AI response as a stream of text chunks
        and save the complete response as an assistant message.
        """

        messages = self._build_messages(
            conversation,
            exclude_message_id=user_message.id,
        )

        chunks = self.ai_service.generate_stream(
            user_message.content,
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
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