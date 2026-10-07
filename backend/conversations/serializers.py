from rest_framework import serializers
from .models import Conversation, Message
from people.models import Person


class ConversationSerializer(serializers.ModelSerializer):
    person = serializers.PrimaryKeyRelatedField(
        queryset=Person.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "person",
            "is_archived",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request is not None and request.user.is_authenticated:
            self.fields["person"].queryset = Person.objects.filter(
                user=request.user,
                is_active=True,
            )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Conversation title cannot be empty."
            )

        return value

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "sender_type",
            "content",
            "is_read",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_read",
        ]

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Message content cannot be empty."
            )    
        return value