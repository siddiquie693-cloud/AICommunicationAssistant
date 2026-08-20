from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

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
        return queryset.order_by("created_at")

    def perform_create(self, serializer):
        conversation = self.get_conversation()

        serializer.save(
            conversation=conversation,
        )

class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            conversation__user=self.request.user,
            conversation_id=self.kwargs["conversation_id"],
        )
