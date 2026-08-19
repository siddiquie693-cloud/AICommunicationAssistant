from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
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
            user=self.request.user
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

        return queryset.order_by("-created_at")    

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )

class ConversationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
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