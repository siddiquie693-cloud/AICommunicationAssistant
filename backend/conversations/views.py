from django.http import StreamingHttpResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ai.providers.exceptions import AIProviderError
from ai.translation.exceptions import TranslationProviderError
from .speech_to_text_serializers import SpeechToTextSerializer
from ai.speech_to_text.exceptions import SpeechToTextProviderError
from ai.text_to_speech.exceptions import TextToSpeechProviderError
from .text_to_speech_serializers import TextToSpeechSerializer

from .translation_serializers import TranslationSerializer
from .models import Conversation, Message
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from conversations.services.ai_conversation_service import (
    AIConversationService,
)

from .pagination import (
    ConversationPagination,
    MessagePagination,
)
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
)

class ConversationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ConversationPagination

    def get_queryset(self):
        queryset = Conversation.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        )

        archived = self.request.query_params.get(
            "archived"
        )

        if archived == "true":
            queryset = queryset.filter(
                is_archived=True
            )
        else:
            queryset = queryset.filter(
                is_archived=False
            )

        search = self.request.query_params.get(
            "search"
        )

        if search:
            queryset = queryset.filter(
                title__icontains=search
            )

        ordering = self.request.query_params.get(
            "ordering",
            "-created_at",
        )

        allowed_orderings = {
            "created_at",
            "-created_at",
        }

        if ordering not in allowed_orderings:
            ordering = "-created_at"

        return queryset.order_by(
            ordering,
            "-id" if ordering == "-created_at" else "id",
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )

class ConversationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True,
        )

    def destroy(self, request, *args, **kwargs):
        conversation = self.get_object()

        conversation.deleted_at = timezone.now()
        conversation.save(
            update_fields=["deleted_at"]
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class ConversationRestoreAPIView(generics.GenericAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            id=kwargs["pk"],
            user=request.user,
        )

        if conversation.deleted_at is None:
            return Response(
                {
                    "detail": "Conversation is already active."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation.deleted_at = None
        conversation.save(
            update_fields=["deleted_at"]
        )

        serializer = self.get_serializer(conversation)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ConversationTrashListAPIView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ConversationPagination

    def get_queryset(self):
        queryset = Conversation.objects.filter(
            user=self.request.user,
            deleted_at__isnull=False,
        )

        search = self.request.query_params.get(
            "search"
        )

        if search:
            queryset = queryset.filter(
                title__icontains=search
            )
        return queryset.order_by(
            "-deleted_at",
            "-id",
        )

class MessageListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MessagePagination

    def get_conversation(self):
        return get_object_or_404(
            Conversation,
            id=self.kwargs["conversation_id"],
            user=self.request.user,
            deleted_at__isnull=True,
        )

    def get_queryset(self):
        conversation = self.get_conversation()

        queryset = conversation.messages.all()

        search = self.request.query_params.get(
            "search"
        )

        if search:
            queryset = queryset.filter(
                content__icontains=search
            )
        ordering = self.request.query_params.get(
            "ordering",
            "created_at",
        )

        allowed_orderings = {
            "created_at",
            "-created_at",
        }

        if ordering not in allowed_orderings:
            ordering = "created_at"

        return queryset.order_by(
            ordering,
            "id" if ordering == "created_at" else "-id",
        )

    def create(self, request, *args, **kwargs):
        try:
            return super().create(
                request,
                *args,
                **kwargs,
            )
        except AIProviderError:
            return Response(
                {
                    "detail": "AI service is temporarily unavailable.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def perform_create(self, serializer):
        conversation = self.get_conversation()
        user_message = serializer.save(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
        )
        ai_service = AIConversationService()
        ai_service.generate_response(
            conversation=conversation,
            user_message=user_message,
        )

class AIMessageStreamAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            id=kwargs["conversation_id"],
            user=request.user,
            deleted_at__isnull=True,
        )

        content = request.data.get("content", "")
        preferred_language = request.data.get("preferred_language")

        if not isinstance(content, str) or not content.strip():
            return Response(
                {
                    "detail": "Message content cannot be empty.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_message = Message.objects.create(
            conversation=conversation,
            sender_type=Message.SENDER_USER,
            content=content.strip(),
        )

        ai_service = AIConversationService()

        def stream_response():
            try:
                yield from ai_service.generate_stream(
                    conversation=conversation,
                    user_message=user_message,
                    preferred_language=preferred_language,
                )
            except AIProviderError as exc:
                yield (
                    "AI service is temporarily unavailable. "
                    "Please try again later."
                )

        return StreamingHttpResponse(
            stream_response(),
            content_type="text/plain",
        )

class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user,
            conversation_id=self.kwargs["conversation_id"],
            conversation__deleted_at__isnull=True,
        )

class MessageReadAPIView(generics.GenericAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation,
            id=kwargs["conversation_id"],
            user=request.user,
            deleted_at__isnull=True,
        )

        message = get_object_or_404(
            Message,
            id=kwargs["pk"],
            conversation=conversation,
        )

        message.is_read = True
        message.save(
            update_fields=["is_read"]
        )

        serializer = self.get_serializer(message)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class TranslationAPIView(generics.GenericAPIView):
    serializer_class = TranslationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        translation_service = AIConversationService()

        try:
            translated_text = translation_service.translate_text(
                serializer.validated_data["text"],
                source_language=serializer.validated_data.get(
                    "source_language"
                ),
                target_language=serializer.validated_data[
                    "target_language"
                ],
            )
        except TranslationProviderError:
            return Response(
                {
                    "error": {
                        "code": "translation_provider_error",
                        "message": "Translation service is currently unavailable.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "translated_text": translated_text,
            },
            status=status.HTTP_200_OK,
        )

class SpeechToTextAPIView(generics.GenericAPIView):
    serializer_class = SpeechToTextSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        speech_to_text_service = AIConversationService()

        try:
            transcribed_text = (
                speech_to_text_service.transcribe_audio(
                    serializer.validated_data["audio"],
                    language=serializer.validated_data.get(
                        "language"
                    ),
                )
            )
        except SpeechToTextProviderError:
            return Response(
                {
                    "error": {
                        "code": "speech_to_text_provider_error",
                        "message": "Speech-to-text service is currently unavailable.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )    

        return Response(
            {
                "transcribed_text": transcribed_text,
            },
            status=status.HTTP_200_OK,
        )   

class TextToSpeechAPIView(generics.GenericAPIView):
    serializer_class = TextToSpeechSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        text_to_speech_service = AIConversationService()

        try:
            audio_data = (
                text_to_speech_service.synthesize_speech(
                    serializer.validated_data["text"],
                    language=serializer.validated_data.get(
                        "language"
                    ),
                    voice=serializer.validated_data.get(
                        "voice"
                    ),
                )
            )
        except TextToSpeechProviderError:
            return Response(
                {
                    "error": {
                        "code": "text_to_speech_provider_error",
                        "message": "Text-to-speech service is currently unavailable.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return HttpResponse(
            audio_data,
            content_type="audio/wav",
        )     