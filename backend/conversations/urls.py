from django.urls import path

from .views import (
    ConversationDetailAPIView,
    ConversationListCreateAPIView,
    ConversationRestoreAPIView,
    ConversationTrashListAPIView,
    MessageListCreateAPIView,
    MessageDetailAPIView,
    MessageReadAPIView,
)

urlpatterns = [
    path("", 
        ConversationListCreateAPIView.as_view(),
        name="conversation-list-create",
    ),
    path(
        "trash/",
        ConversationTrashListAPIView.as_view(),
        name="conversation-list-create",
    ),
    path("<int:pk>/",
        ConversationDetailAPIView.as_view(),
        name="conversation-detail",
    ),
    path(
        "<int:pk>/restore/",
        ConversationRestoreAPIView.as_view(),
        name="conversation-restore",
    ),
    path(
        "<int:conversation_id>/messages/",
        MessageListCreateAPIView.as_view(),
        name="message-list-create",
    ),
    path(
        "<int:conversation_id>/messages/<int:pk>/",
        MessageDetailAPIView.as_view(),
        name="message-detail",
    ),
    path(
        "<int:conversation_id>/messages/<int:pk>/read/",
        MessageReadAPIView.as_view(),
        name="message-read",
    ),
]