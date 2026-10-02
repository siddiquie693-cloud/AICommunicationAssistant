from rest_framework import serializers

from .models import Memory


class MemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = [
            "id",
            "content",
            "memory_type",
            "importance",
            "expires_at",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Memory content cannot be empty."
            )

        return value