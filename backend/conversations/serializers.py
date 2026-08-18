from rest_framework import serializers
from .models import Conversation

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "is_archived",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]