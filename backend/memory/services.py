from django.db.models import Q
from django.utils import timezone

from .models import Memory


class MemoryService:
    """Manages persistent personal memories for authenticated users."""

    @staticmethod
    def create_memory(
        *,
        user,
        content,
        memory_type,
        importance=3,
        expires_at=None,
        metadata=None,
    ):
        return Memory.objects.create(
            user=user,
            content=content,
            memory_type=memory_type,
            importance=importance,
            expires_at=expires_at,
            metadata=metadata or {},
        )

    @staticmethod
    def get_memory(*, user, memory_id):
        return Memory.objects.filter(
            id=memory_id,
            user=user,
        ).first()

    @staticmethod
    def list_memories(*, user, include_inactive=False):
        queryset = Memory.objects.filter(user=user)

        if not include_inactive:
            queryset = queryset.filter(is_active=True)

        return queryset

    @staticmethod
    def list_active_memories(*, user):
        now = timezone.now()

        return Memory.objects.filter(
            user=user,
            is_active=True,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

    @staticmethod
    def update_memory(*, user, memory_id, **updates):
        memory = Memory.objects.filter(
            id=memory_id,
            user=user,
        ).first()

        if memory is None:
            return None

        allowed_fields = {
            "content",
            "memory_type",
            "importance",
            "expires_at",
            "is_active",
            "metadata",
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(memory, field, value)

        memory.full_clean()
        memory.save()

        return memory

    @staticmethod
    def deactivate_memory(*, user, memory_id):
        memory = Memory.objects.filter(
            id=memory_id,
            user=user,
        ).first()

        if memory is None:
            return None

        memory.is_active = False
        memory.save(update_fields=["is_active", "updated_at"])

        return memory

    @staticmethod
    def delete_memory(*, user, memory_id):
        memory = Memory.objects.filter(
            id=memory_id,
            user=user,
        ).first()

        if memory is None:
            return False

        memory.delete()
        return True