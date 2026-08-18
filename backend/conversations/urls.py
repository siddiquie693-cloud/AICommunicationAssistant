from django.urls import path

from .views import (
    ConversationDetailAPIView,
    ConversationListCreateAPIView,
    MessageListCreateAPIView,
)

urlpatterns = [
    path("", 
        ConversationListCreateAPIView.as_view(),
        name="conversation-list-create",
    ),
    path("<int:pk>/",
        ConversationDetailAPIView.as_view(),
        name="conversation-detail",
    ),
    path(
        "<int:conversation_id>/messages/",
        MessageListCreateAPIView.as_view(),
        name="message-list-create",
    ),
]